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

"""Validations involving section member.python

What is left here is about the license a manifest declares. The qiskit dependency a
manifest declares is read by the `[Q0*]` check ups in `checkup_general.py`, which ask the
same questions of a published release and of a requirements file: three copies of one
assertion is what they replaced.
"""

# pylint: disable=invalid-name,missing-function-docstring

import pytest


@pytest.fixture(autouse=True)
def skip_python(member):
    """Skip if there is no python section to look at"""
    if not member.python:
        pytest.skip("No python section")
    yield member


def checkup_S00(member, subtests, explained):
    for package in member.python:
        place = f"python:{package.package_name}"
        with subtests.test(msg=place), explained(place):
            if package.license is None:
                pytest.skip(f"No member.python.{package.package_name}.license")
            assert (
                package.license.is_osi_approved()
            ), f"member.python.{package.package_name}.license is not OSI-approved"
