"""Validations involving section member.github"""

# pylint: disable=missing-function-docstring, redefined-outer-name

import pytest


@pytest.fixture
def skip_github(member):
    if member.github is None:
        pytest.skip("No github section")
    yield member


def test_archived(member):
    """G05"""
    if hasattr(member.github, "archived") and member.github.archived:
        assert hasattr(
            member, "status"
        ), "GitHub repository archived, so member.status must exist and be `archived`"
        assert (
            member.status == "archived"
        ), "GitHub repository archived, so member.status must be `archived`"
