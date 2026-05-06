"""Validations involving section member.pypi


LT (<): Less Than
GT (>): Greater Than
GE (≥): Greater Than or Equal To
LE (≤): Less Than or Equal To

"""

# pylint: disable=invalid-name

import pytest


@pytest.fixture
def skip_pypi(member):
    """Skip if no pypi seciton"""
    if member.pypi is None:
        pytest.skip("No pypi section")
    yield member


def test_PQ1(member):
    """Be installable with qiskit>=1.0"""
    for pypi_package in member.pypi.values():
        if pypi_package.compatible_with_qiskit_v1 is None:
            pytest.skip("member.pypi.*.compatible_with_qiskit_v1")
        assert pypi_package.compatible_with_qiskit_v1


def test_PQ2(member, subtests):
    """Be installable with qiskit>=2.0"""
    for pypi_package in member.pypi.values():
        with subtests.test(pypi_package=pypi_package.package_name):
            if pypi_package.compatible_with_qiskit_v2 is None:
                pytest.skip("member.pypi.*.compatible_with_qiskit_v2")
            assert (
                pypi_package.compatible_with_qiskit_v2
            ), f"Python package {pypi_package.package_name} is not compatible with Qiskit SDK v2"
