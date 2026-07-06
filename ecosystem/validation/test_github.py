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

import pytest


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
