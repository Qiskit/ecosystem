"""Tooling for validation tests
See https://docs.pytest.org/en/stable/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files  # pylint: disable=line-too-long
"""

import pytest


def pytest_configure(config):
    """Add a test mark called previously_failed(since)"""
    config.addinivalue_line(
        "markers", "previously_failed(since): mark test as previously failed"
    )


class ValidationReport:
    # pylint: disable=missing-function-docstring, missing-class-docstring

    def __init__(self, member):
        self._member = member
        self.collected = 0
        self.exitcode = 0
        self.passed = []
        self.failed = []
        self.xfailed = []
        self.skipped = []
        self.internalerror = []

    @property
    def xfails(self):
        return {
            checkdata.checker: checkdata.xfailed for checkdata in self._member.xfails
        }

    @property
    def previous_failures(self):
        return {
            checkdata.checker: checkdata.since
            for checkdata in self._member.checks.values()
            if checkdata.since
        }

    def pytest_itemcollected(self, item):
        # pylint: disable=protected-access
        item._nodeid = "/".join(item.nodeid.split("/")[2:])

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):  # pylint: disable=unused-argument

        outcome = yield
        report = outcome.get_result()
        if report.when == "call":
            if report.passed:
                self.passed.append(report)
            elif report.failed:
                for mark in item.iter_markers():
                    setattr(report, mark.name, mark)
                self.failed.append(report)
            elif hasattr(report, "wasxfail") and report.wasxfail:
                self.xfailed.append(report)
            else:
                self.skipped.append(report)
        elif report.when == "setup" and report.failed:
            # internal error: the test failed to run because it is somehow wrongly set
            self.internalerror.append(report)

    def pytest_collection_modifyitems(self, items):
        self.collected = len(items)
        for item in items:
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
