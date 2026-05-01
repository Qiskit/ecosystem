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
            member, "support"
        ), "GitHub repository archived, so member.support must exist and be `archived`"
        assert (
            member.support == "archived"
        ), "GitHub repository archived, so member.support must be `archived`"
