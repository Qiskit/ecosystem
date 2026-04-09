"""Description validations"""

# pylint: disable=missing-function-docstring

import pytest


def test_description_len_135(member):
    if member.description is None:
        pytest.skip("No member.description")
    assert (
        len(member.description) <= 135
    ), f"Description is {len(member.description)}-character long"
