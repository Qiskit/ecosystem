// This code is part of Qiskit.
//
// (C) Copyright IBM 2026
//
// This code is licensed under the Apache License, Version 2.0. You may
// obtain a copy of this license in the LICENSE.txt file in the root directory
// of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
//
// Any modifications or derivative works of this code must retain this
// copyright notice, and modified files need to carry a notice indicating
// that they have been altered from the originals.

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
