# This code is part of Qiskit.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""Tests for ecosystem/validation/conftest.py, the plugin a validation run reports through

The reports are built here rather than by running pytest: what these cover is which bucket a
report lands in, and the only way to get the interesting ones out of a real run is to write a
check up that fails in a particular way.
"""

from datetime import date, timedelta
from unittest import TestCase

from ecosystem.check import CheckData, ChecksToml
from ecosystem.member import Member
from ecosystem.validation.conftest import ValidationReport

NODE = "checkup_general.py::checkup_Q03"


class Context:  # pylint: disable=too-few-public-methods
    """What `pytest-subtests` attaches to a subtest's report"""

    def __init__(self, msg):
        self.msg = msg
        self.kwargs = {}


class Report:  # pylint: disable=too-few-public-methods
    """A report of the `call` phase, as `pytest_runtest_logreport` receives it"""

    def __init__(self, outcome, longrepr=None, place=None, nodeid=NODE):
        self.when = "call"
        self.nodeid = nodeid
        self.outcome = outcome
        self.longrepr = longrepr
        self.longreprtext = longrepr or ""
        if place is not None:
            self.context = Context(place)

    @property
    def passed(self):
        """pytest's own report property"""
        return self.outcome == "passed"

    @property
    def failed(self):
        """pytest's own report property"""
        return self.outcome == "failed"


def plugin(member=None):
    """The plugin, for a member with no check ups unless one is given"""
    return ValidationReport(
        member or Member(name="banana", url="https://github.com/o/r"), ChecksToml()
    )


class TestTheSubtestBuckets(TestCase):
    """A report is bucketed with the place it is about, when it is about one"""

    def test_a_failing_subtest_carries_its_place(self):
        """Which is what `CheckData.from_report` reads to know what the record is about"""
        report = plugin()
        report.pytest_runtest_logreport(Report("failed", "AssertionError: x", "pypi:a"))

        self.assertEqual(["pypi:a"], [r.subtest for r in report.failed])

    def test_the_subtests_summary_is_not_a_record(self):
        """`contains N failed subtests` is about no place, and is not an assertion message"""
        report = plugin()
        report.pytest_runtest_logreport(Report("failed", "AssertionError: x", "pypi:a"))
        report.pytest_runtest_logreport(Report("failed", "contains 1 failed subtest"))

        self.assertEqual(["AssertionError: x"], [r.longreprtext for r in report.failed])

    def test_a_failure_outside_the_subtests_is_still_recorded(self):
        """A check up that blows up after its first subtest is failing, not passing"""
        report = plugin()
        report.pytest_runtest_logreport(Report("passed", place="pypi:a"))
        report.pytest_runtest_logreport(Report("failed", "RuntimeError: boom"))

        self.assertEqual(
            ["RuntimeError: boom"], [r.longreprtext for r in report.failed]
        )

    def test_a_check_up_with_no_subtests_is_bucketed_as_before(self):
        """Most check ups: one report, no place, nothing to drop"""
        report = plugin()
        report.pytest_runtest_logreport(Report("failed", "AssertionError: y"))

        self.assertEqual(["AssertionError: y"], [r.longreprtext for r in report.failed])


class TestWhatReachesPytest(TestCase):
    """The two properties the plugin exposes to a run: the explanations and the clocks"""

    @staticmethod
    def member(*records):
        """A member whose [Q03] holds those records"""
        member = Member(name="banana", url="https://github.com/o/r")
        member.checks = {"Q03": list(records)}
        return member

    def test_only_a_place_less_explanation_can_be_a_marker(self):
        """A marker covers the whole function, so a per-place one is applied in the subtest"""
        member = self.member(
            CheckData("Q03", xfailed="about the member"),
            CheckData("Q03", subtest="pypi:a", xfailed="about one distribution"),
        )
        self.assertEqual(
            {"checkup_general.py::checkup_Q03": "about the member"},
            plugin(member).xfails,
        )

    def test_the_clock_is_the_earliest_unexplained_place(self):
        """An explained place is not a date anybody is counting towards"""
        member = self.member(
            CheckData(
                "Q03",
                subtest="pypi:old",
                since=date(2026, 1, 1),
                xfailed="explained",
                xfailed_until=date.today() + timedelta(days=30),
            ),
            CheckData("Q03", subtest="requirements:new.txt", since=date(2026, 9, 1)),
        )
        self.assertEqual(
            {"checkup_general.py::checkup_Q03": date(2026, 9, 1)},
            plugin(member).previous_failures,
        )

    def test_a_check_up_with_nothing_unexplained_has_no_clock(self):
        """Every place is excused, so there is no cure period to report to the run"""
        member = self.member(
            CheckData(
                "Q03",
                subtest="pypi:a",
                since=date(2026, 1, 1),
                xfailed="explained",
                xfailed_until=date.today() + timedelta(days=30),
            )
        )
        self.assertEqual({}, plugin(member).previous_failures)
