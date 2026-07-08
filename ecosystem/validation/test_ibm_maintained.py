# This code is part of Qiskit.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Validations involving section member.ibm_maintained"""

# pylint: disable=invalid-name

import pytest

ibm_controlled_gh_org = ["qiskit", "qiskit-community", "openqasm"]


@pytest.fixture(autouse=True)
def skip_ibm_maintained(member):
    """Skip if no IBM maintained project"""
    if not member.ibm_maintained:
        pytest.skip("Not IBM maintained project")
    yield member


def test_I00(member):
    """IBM maintained projects should live in IBM-controlled GitHub organizations"""
    assert (
        member.github.owner.lower() in ibm_controlled_gh_org
    ), "ibm-maintained project not in ibm-controlled GitHub org"
