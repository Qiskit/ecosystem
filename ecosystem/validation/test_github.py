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

"""Validations involving section member.github"""

# pylint: disable=invalid-name,missing-function-docstring

from datetime import date
from dateutil.relativedelta import relativedelta

import pytest

from ecosystem.serializable import parse_date


@pytest.fixture(autouse=True)
def skip_github(member):
    """Skip if no github section"""
    if member.github is None:
        pytest.skip("No github section")
    yield member


def test_G05(member):
    """GitHub repository is archived?"""
    if hasattr(member.github, "archived") and member.github.archived:
        assert hasattr(
            member, "maturity"
        ), "GitHub repository archived, so member.maturity must exist and be `as-is`"
        assert member.maturity in [
            "as-is",
            "unmaintaned",
        ], "GitHub repository archived and member.maturity is not `as-is` or `unmaintaned`"


def test_G06(member):
    """Have maintainer activity within the last 6 months"""
    if member.maturity == "as-is":
        pytest.skip("`as-is` projects are exempt from activity checks")

    last_activity = member.github.last_activity
    if last_activity is None:
        pytest.skip("No member.github.last_activity date")

    relative = relativedelta(date.today(), last_activity)
    months_difference = (relative.years * 12) + relative.months

    assert months_difference <= 6, (
        f"Last activity was {months_difference} months ago, which is more "
        "than 6 months ago. Please update the GitHub repository or set "
        "member.maturity to `as-is`."
    )


def test_G07(member):
    """Have last commit within the last 18 months"""
    if member.maturity == "as-is":
        pytest.skip("`as-is` projects are exempt from activity checks")

    last_commit = member.github.last_commit
    if last_commit is None:
        pytest.skip("No member.github.last_commit date")

    relative = relativedelta(date.today(), last_commit)
    months_difference = (relative.years * 12) + relative.months

    assert months_difference <= 18, (
        f"Last commit was {months_difference} months ago, which is more "
        "than 18 months ago. Please update the GitHub repository or set "
        "member.maturity to `as-is`."
    )


def test_G08(member):
    """Unmaintaned projects should archive their GitHub repository"""
    if member.maturity in ["deprecated", "unmaintaned"]:
        assert (
            member.github.archived
        ), "unsupported project should have an archived GitHub org"


def test_G09(member):
    if str(member.github.license) in ["None", "Other"]:
        assert (
            member.github.license.license_name is not None
        ), "member.github.license not detected"
        assert (
            member.github.license.license_name != "Other"
        ), "member.github.license not detected"


def test_G10(member):
    if member.github.license:
        if str(member.github.license) in ["None", "Other"]:
            pytest.skip("No member.github.license, already covered by [G09]")
        assert (
            member.github.license.is_osi_approved()
        ), "member.github.license is not OSI-approved"
