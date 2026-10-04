# This code is part of Qiskit.
#
# (C) Copyright IBM 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


"""Tooling for validation tests
See https://docs.pytest.org/en/stable/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files  # pylint: disable=line-too-long
"""

from contextlib import contextmanager

import pytest


def pytest_configure(config):
    """Add a test mark called previously_failed(since)"""
    config.failed_checkups = {}
    config.addinivalue_line(
        "markers", "previously_failed(since): mark test as previously failed"
    )


class ValidationReport:
    # pylint: disable=missing-function-docstring, missing-class-docstring

    def __init__(self, member, checktoml):
        self._member = member
        #: the node ids that reported subtests, so that their function-level report is not
        #: bucketed as well: `pytest-subtests` flips it to failed after the fact, with
        #: `contains N failed subtests` where a check up message is expected
        self._subtested = set()
        self.collected = 0
        self.exitcode = 0
        self.passed = []
        self.failed = []
        self.xfailed = []
        self.skipped = []
        self.internalerror = []
        self.checktoml = checktoml

    @property
    def xfails(self):
        """The explanations that can be a marker on the check up function.

        Only the ones that are about the member as a whole. An explanation for one place
        (`checkdata.subtest`) cannot be a marker: a marker is attached to the function, so it
        would cover every subtest of it, including the places that pass. Those are applied by
        the `explained` fixture instead, inside the subtest that failed.
        """
        return {
            checkdata.checker: checkdata.xfailed
            for checkdata in self._member.xfails
            # a source-based check up has no checker: it is not the result of a test
            if getattr(checkdata, "checker", None) and not checkdata.subtest
        }

    @property
    def previous_failures(self):
        """When each check up started failing, for the `previously_failed` marker.

        The earliest of a check up's records: it is the one whose cure period runs out first,
        and it is what the aggregating check ups ([Q20], [G00], [001]) have to see, since they
        ask whether the cure period of what they wait on has expired.
        """
        since_by_checker = {}
        for checkdata in self._member.failing_checkups + self._member.xfails:
            checker = getattr(checkdata, "checker", None)
            if not checkdata.since or not checker:
                # a source-based check up has no checker: it is not the result of a test
                continue
            stored = since_by_checker.get(checker)
            since_by_checker[checker] = (
                checkdata.since if stored is None else min(stored, checkdata.since)
            )
        return since_by_checker

    def pytest_itemcollected(self, item):
        # pylint: disable=protected-access
        item._nodeid = "/".join(item.nodeid.split("/")[2:])

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):  # pylint: disable=unused-argument
        """Annotates a report with what only the item knows, and collects setup failures.

        The reports themselves are bucketed in `pytest_runtest_logreport`, which is the only
        hook that sees which subtest a report is about.
        """
        outcome = yield
        report = outcome.get_result()
        if report.when == "call" and report.failed:
            for mark in item.iter_markers():
                setattr(report, mark.name, mark)
            item.config.failed_checkups[item.nodeid] = report
        elif report.when == "setup" and report.failed:
            # internal error: the test failed to run because it is somehow wrongly set
            self.internalerror.append(report)

    def pytest_runtest_logreport(self, report):
        """Buckets a report, with the place it is about when it is one subtest of a check up.

        This rather than `pytest_runtest_makereport`, which structurally cannot tell one
        subtest from another: `pytest-subtests` builds its report from the *parent* item, so
        every subtest shares the function's node id, and the `SubtestReport` that carries the
        identity is a new object delivered only here.
        """
        if report.when != "call":
            return
        context = getattr(report, "context", None)
        if context is not None:
            # `msg` rather than one of the `kwargs`, whose values arrive `saferepr`-ed
            report.subtest = context.msg
            self._subtested.add(report.nodeid)
        elif report.nodeid in self._subtested:
            # the function-level report of a check up that ran subtests, which says
            # `contains N failed subtests` and is not about any one place
            return
        if hasattr(report, "wasxfail") and report.wasxfail:
            # an xfail that passed anyway is nothing to record, as before
            if not report.passed:
                self.xfailed.append(report)
        elif report.passed:
            self.passed.append(report)
        elif report.failed:
            self.failed.append(report)
        else:
            self.skipped.append(report)

    def pytest_collection_modifyitems(self, items):
        self.collected = len(items)
        for item in items:
            if (
                self.checktoml.checkup(self.checktoml.id_by_pytest_node(item.nodeid))[
                    "importance"
                ]
                == "LEGACY"
            ):
                item.add_marker(pytest.mark.skip(reason="legacy check"))
            if item.nodeid in self.xfails:
                item.add_marker(pytest.mark.xfail(reason=self.xfails[item.nodeid]))
            if item.nodeid in self.previous_failures:
                item.add_marker(
                    pytest.mark.previously_failed(
                        since=self.previous_failures[item.nodeid]
                    )
                )

    def pytest_terminal_summary(
        self, terminalreporter, exitstatus
    ):  # pylint: disable=unused-argument
        self.exitcode = exitstatus.value if hasattr(exitstatus, "value") else exitstatus

    @pytest.fixture
    def member(self):
        return self._member

    @pytest.fixture
    def explained(self, request):
        """A context manager that turns one place's failure into an xfail, when explained.

        For a check up that reads several places, an explanation is about one of them (see
        `self.xfails`), so it is applied here, inside the subtest, rather than as a marker on
        the function. The assertion runs either way, which is what makes a place that got
        fixed stop being recorded instead of being reported as an XPASS.
        """
        checkup_id = request.node.name.removeprefix("checkup_")

        @contextmanager
        def explained_place(place):
            try:
                yield
            except AssertionError:
                reason = self._member.explanation_for(checkup_id, place)
                if reason:
                    pytest.xfail(reason)
                raise

        return explained_place
