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

"""Validations involving section member.pypi"""

# pylint: disable=invalid-name,missing-function-docstring

import pytest


@pytest.fixture(autouse=True)
def skip_pypi(member):
    """Skip if no pypi seciton"""
    if member.pypi is None:
        pytest.skip("No pypi section")
    yield member


def test_PQ1(member, subtests):
    """Be installable with qiskit>=1.0"""
    for pypi_package in member.pypi.values():
        with subtests.test(pypi_package=pypi_package.package_name):
            if pypi_package.compatible_with_qiskit_v1 is None:
                pytest.skip(
                    f"No member.pypi.{pypi_package.package_name}.compatible_with_qiskit_v1"
                )
            assert (
                pypi_package.compatible_with_qiskit_v1
            ), f"Python package {pypi_package.package_name} is not compatible with Qiskit SDK v1"


def test_PQ2(member, subtests):
    """Be installable with qiskit>=2.0"""
    for pypi_package in member.pypi.values():
        with subtests.test(pypi_package=pypi_package.package_name):
            if pypi_package.compatible_with_qiskit_v2 is None:
                pytest.skip(
                    f"No member.pypi.{pypi_package.package_name}.compatible_with_qiskit_v2"
                )
            assert (
                pypi_package.compatible_with_qiskit_v2
            ), f"Python package {pypi_package.package_name} is not compatible with Qiskit SDK v2"

def test_P10(member):
    for pypi_package in member.pypi.values():
        assert pypi_package.compatible_with_qiskit(
            3
        ), f"Python package {pypi_package.package_name} declared itself compatible to a not-yet-released major version of Qiskit"


def test_P11(member):
    """Production-ready projects should have, at least, one stable Python package"""
    if member.maturity not in ["production-ready", "bugfixing only"]:
        pytest.skip("member.maturity not in [production ready, bugfixing only]")

    experimental_packages = []
    stable_packages = []
    for pypi_package in member.pypi.values():
        if getattr(pypi_package, "development_status", None) in [
            "1 - Planning",
            "2 - Pre-Alpha",
            "3 - Alpha",
            "4 - Beta",
        ]:
            experimental_packages.append(pypi_package.package_name)
        else:
            stable_packages.append(pypi_package.package_name)

    if len(experimental_packages) + len(stable_packages) == 0:
        pytest.skip("No member.pypi.*.development_status")

    assert (
        len(stable_packages) != 0
    ), "At least one python package should declare a stable development status classifier"


def test_P12(member):
    for pypi_package in member.pypi.values():
        if pypi_package.license is None:
            assert (
                pypi_package.license is not None
            ), f"member.pypi.{pypi_package.package_name} does not have a declared license"


def test_P13(member):
    for pypi_package in member.pypi.values():
        if pypi_package.license is not None:
            assert (
                pypi_package.license.is_osi_approved()
            ), f"member.pypi.{pypi_package.package_name}.license is not OSI-approved"
