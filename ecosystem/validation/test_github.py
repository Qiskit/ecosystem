"""Validations involving section member.github"""

# pylint: disable=invalid-name

import pytest


@pytest.fixture
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
        assert (
            member.maturity == "as-is"
        ), "GitHub repository archived and member.maturity is not `as-is`"
