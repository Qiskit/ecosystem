"""Validation module"""

import pytest

from ecosystem.check import ChecksToml
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
  
"""


def validate_member(member, tests_to_run=None, verbose_level=None):
    """Runs all the validation for a member
    verbose_level: -v, -vv, -q
    """
    report = ValidationReport(member, ChecksToml())
    if verbose_level is None:
        verbose_level = "-q"
    if tests_to_run is None:
        tests_to_run = ""
    pytest.main(
        [
            f"ecosystem/validation/{tests_to_run}",
            "--tb=no",
            "-rN",
            verbose_level,
            "--no-header",
        ],
        plugins=[report],
    )
    return report
