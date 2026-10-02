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

"""Validations involving section member.requirements

The counterparts of the `member.python` check ups for a repository that declares no
packaging manifest at all. There is no distribution to name, so these are about the
repository itself: what its requirements file says is the only statement the project
makes about which Qiskit it runs against.
"""

# pylint: disable=invalid-name,missing-function-docstring

import pytest


@pytest.fixture(autouse=True)
def skip_requirements(member):
    """Skip if there is no requirements section to look at"""
    if not member.requirements:
        pytest.skip("No requirements section")
    yield member


def checkup_R01(member):
    """Be installable with qiskit>=2.0 from the requirements file"""
    requirements = member.requirements
    if requirements.compatible_with_qiskit_v2 is None:
        pytest.skip("No member.requirements.compatible_with_qiskit_v2")
    assert requirements.compatible_with_qiskit_v2, (
        f"The qiskit requirement in {requirements.file} "
        "is not compatible with Qiskit SDK v2"
    )


def checkup_R02(member):
    requirements = member.requirements
    assert not requirements.compatible_with_qiskit(3), (
        f"The qiskit requirement in {requirements.file} "
        "allows a not-yet-released major version of Qiskit"
    )
