"""Validation module"""

import pytest

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
 
 members handle of checks:
 
# a way to skip checks. Give an explanation (or a link to the discussion)
[checks.010]   
xfailed =  "skip this because that"

# this check failed. since is when that failure was detected 
# (it might be relevant for warnings)
[checks.001]  
details = "explain why this member fails this check"
since = 2025-10-22T14:47:06Z
 
"""


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

    @property
    def xfails(self):
        return {
            checkdata.checker: checkdata.xfailed for checkdata in self._member.xfails
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

    def pytest_terminal_summary(
        self, terminalreporter, exitstatus
    ):  # pylint: disable=unused-argument
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
