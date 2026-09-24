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

from . import ibm_controlled_gh_org


@pytest.fixture(autouse=True)
def skip_github(member):
    """Skip if no github section"""
    if member.github is None:
        pytest.skip("No github section")
    yield member


def test_G05(member):
    """GitHub repository is archived?"""
    if member.maturity in ["as-is"]:
        pytest.skip("projects with maturity 'as-is' are exempt")
    else:
        assert not (
            hasattr(member.github, "archived") and member.github.archived
        ), f"GitHub repository {member.github.url} archived and project is not `as-is`"


def test_G06(member):
    """Have maintainer activity within the last 6 months"""
    if member.unmaintained:
        pytest.skip("projects with no maintenance expectations are exempt")

    last_activity = member.github.last_activity
    if last_activity is None:
        pytest.skip("No member.github.last_activity date")

    relative = relativedelta(date.today(), last_activity)
    months_difference = (relative.years * 12) + relative.months

    assert months_difference <= 6, (
        "Last activity was more then 6 months ago, which probably means that the project "
        "is not actively maintained and/or used. Maybe `member.maturity` should be set as `as-is`?"
    )


def test_G07(member):
    """Have last commit within the last 12 months"""
    if member.unmaintained:
        pytest.skip("projects with no maintenance expectations are exempt")

    if member.age_in_months is None:
        pytest.skip("member.age_in_months is None")

    relative = relativedelta(date.today(), member.github.last_commit)
    months_difference = (relative.years * 12) + relative.months

    assert months_difference <= 12, (
        "Last commit was more than 12 months ago. "
        "This might be a sign of a project that is not actively maintained. "
        "Maybe `member.maturity` should be set as `as-is`"
    )


def test_G12(member):
    """Have last commit within the last (age * 2/3) months.
    See https://github.com/orgs/Qiskit/discussions/58"""
    if member.age_in_months is None:
        pytest.skip("member.age_in_months is None")

    if not member.early:
        pytest.skip(
            f"the repository is {member.age_in_months} months old, not young anymore"
        )

    relative = relativedelta(date.today(), member.github.last_commit)
    months_difference = (relative.years * 12) + relative.months
    window = max(2, member.age_in_months * (2 / 3))

    assert months_difference <= window, (
        "Last commit was more than (project_age * 2/3) months ago. "
        "This might be a sign of a project with good initial momentum that is decelerating."
    )


def test_G08(member):
    """unmaintained projects should archive their GitHub repository"""
    if member.unmaintained:
        assert getattr(
            member.github, "archived", False
        ), "Unmaintained project should have an archived GitHub repository"


def test_G09(member):
    assert hasattr(member.github, "license"), "member.github.license does not exist"

    if member.github.license and str(member.github.license) in ["None", "Other"]:
        assert (
            member.github.license.license_name is not None
        ), "member.github.license not detected"
        assert (
            member.github.license.license_name != "Other"
        ), "member.github.license not detected"


def test_G10(member):
    if hasattr(member.github, "license"):
        if str(member.github.license) in ["None", "Other"]:
            pytest.skip("No member.github.license, already covered by [G09]")
        assert (
            member.github.license.is_osi_approved()
        ), "member.github.license is not OSI-approved"


def test_G11(member):
    """
    unmaintained projects should be archived when the repo is on an IBM-controlled organization"
    """
    if not hasattr(member, "github"):
        pytest.skip("member.github does not exist")
    if member.github.owner.lower() not in ibm_controlled_gh_org:
        pytest.skip("repository is on an IBM-controlled organization")
    archived = member.github.archived if hasattr(member.github, "archived") else False
    if archived:
        pytest.skip("project repository is already archived")
    if member.unmaintained:
        assert archived, "Unmaintained project should live in an archived repository"
