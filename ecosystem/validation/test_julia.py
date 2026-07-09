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

"""Validations involving section member.julia"""

# pylint: disable=invalid-name,missing-function-docstring

import pytest


@pytest.fixture(autouse=True)
def skip_pypi(member):
    """Skip if no julia seciton"""
    if member.julia is None:
        pytest.skip("No julia section")
    yield member

def test_J00(member):
    for julia_package in member.julia.values():
        if julia_package.license is None:
            assert (
                julia_package.license is not None
            ), f"member.julia.{julia_package.package_name} does not have a declared license"


def test_J01(member):
    for julia_package in member.julia.values():
        if julia_package.license is not None:
            assert (
                julia_package.license.is_osi_approved()
            ), f"member.julia.{julia_package.package_name}.license is not OSI-approved"
