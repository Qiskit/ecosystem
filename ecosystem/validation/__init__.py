"""Validation module"""

from dataclasses import dataclass
from tabnanny import verbose

from ecosystem.error_handling import logger

# pylint: disable=pointless-string-statement

"""  
BIG TODO:
MOVE THE VALIDATIONS TO REGULAR PYTHON-BASED TESTS.
THIS CUSTOM VALIDATION DISCOVERY LOOKS TOO MUCH TO UNITTEST DISCOVERY

TODO json:
 - check no member repetition
 - check against schema
TODO member:
 - check license unification naming
 - check that is has a category (or Other, otherwise)
 - if label "research" check if there is a paper
 - if cannot be fixed, collect an "issues" property in the member toml
 - check description length
 - check "website" is not the github repo or similar
"""

import time
import pytest


class ValidationReport:
    def __init__(self, member):
        self._member = member
        self.collected = 0
        self.exitcode = 0
        self.passed = []
        self.failed = []
        self.xfailed = []
        self.skipped = []
        self.xfails = {
            "test_name.py::test_valid_name_no_test_substring": "because life is complicated"
        }

    def pytest_itemcollected(self, item):
        item._nodeid = "/".join(item.nodeid.split("/")[2:])

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        report = outcome.get_result()
        if report.when == "call":
            if report.passed:
                self.passed.append(report)
            elif report.failed:
                self.failed.append(report)
            elif report.wasxfail:
                self.xfailed.append(report)
            else:
                self.skipped.append(report)

    def pytest_collection_modifyitems(self, items):
        self.collected = len(items)
        for item in items:
            if item.nodeid in self.xfails:
                item.add_marker(pytest.mark.xfail(reason=self.xfails[item.nodeid]))

    def pytest_terminal_summary(self, terminalreporter, exitstatus):
        self.exitcode = exitstatus.value if hasattr(exitstatus, "value") else exitstatus

    @pytest.fixture
    def member(self):
        return self._member


def validate_member(member, verbose_level=None):
    """Runs all the validation for a member
    verbose_level: -v, -vv, -q
    """
    report = ValidationReport(member)
    if verbose_level is None:
        verbose_level = "-q"
    pytest.main(
        ["ecosystem/validation", "--tb=no", "-rN", verbose_level, "--no-header"],
        plugins=[report],
    )
    return report
