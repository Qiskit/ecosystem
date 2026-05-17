"""Validations involving section member.pypi"""

# pylint: disable=invalid-name

import pytest


@pytest.fixture
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
    ), "At least one python package should a stable declare development status classifier"
