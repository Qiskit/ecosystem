"""Validation module"""

import pytest
from ecosystem.validation.conftest import ValidationReport

# pylint: disable=pointless-string-statement
"""

TODO json:
 - check no member repetition
 - check against schema
TODO member:
 - check license unification naming
 - check that is has a category (or Other, otherwise)
 - if label "research" check if there is a paper
 - if cannot be fixed, collect an "issues" property in the member toml
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
