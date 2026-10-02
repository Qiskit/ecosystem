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

A member may store several `[[requirements]]` tables, one per file that names qiskit,
and only one of them is a statement of that kind — a dev or lint file is not. So these
read `primary_of` rather than the list: see `ecosystem/requirements.py` for the rule.
"""

# pylint: disable=invalid-name,missing-function-docstring,redefined-outer-name

import pytest

from ecosystem.requirements import primary_of


@pytest.fixture(autouse=True)
def requirements(member):
    """The one requirements section to judge, skipping a member with none"""
    primary = primary_of(member.requirements or [])
    if primary is None:
        pytest.skip("No requirements section")
    yield primary


def checkup_R01(requirements):
    """Be installable with qiskit>=2.0 from the requirements file"""
    if requirements.compatible_with_qiskit_v2 is None:
        pytest.skip("No member.requirements.compatible_with_qiskit_v2")
    assert requirements.compatible_with_qiskit_v2, (
        f"The qiskit requirement in {requirements.file} "
        "is not compatible with Qiskit SDK v2"
    )


def checkup_R02(requirements):
    assert not requirements.compatible_with_qiskit(3), (
        f"The qiskit requirement in {requirements.file} "
        "allows a not-yet-released major version of Qiskit"
    )
