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

The counterparts of the `member.pypi` check ups, for a distribution the repository
declares but does not publish. What they look at is the manifests, so a project can
pass the PyPI check up with its release and fail the one here with its source, which
is the point: the source is what somebody installing from the repository gets.
"""

# pylint: disable=invalid-name,missing-function-docstring

import pytest


@pytest.fixture(autouse=True)
def skip_python(member):
    """Skip if there is no python section to look at"""
    if not member.python:
        pytest.skip("No python section")
    yield member


def checkup_S00(member, subtests):
    for package in member.python:
        with subtests.test(python_package=package.package_name):
            if package.license is None:
                pytest.skip(f"No member.python.{package.package_name}.license")
            assert (
                package.license.is_osi_approved()
            ), f"member.python.{package.package_name}.license is not OSI-approved"


def checkup_S01(member, subtests):
    """Be installable with qiskit>=2.0"""
    for package in member.python:
        with subtests.test(python_package=package.package_name):
            if package.compatible_with_qiskit_v2 is None:
                pytest.skip(
                    f"No member.python.{package.package_name}.compatible_with_qiskit_v2"
                )
            assert package.compatible_with_qiskit_v2, (
                f"The distribution {package.package_name} declared in the repository "
                "is not compatible with Qiskit SDK v2"
            )


def checkup_S02(member, subtests):
    for package in member.python:
        with subtests.test(python_package=package.package_name):
            assert not package.compatible_with_qiskit(3), (
                f"The distribution {package.package_name} declared in the repository "
                "allows a not-yet-released major version of Qiskit"
            )
