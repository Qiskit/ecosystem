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

"""License validations"""

import pytest

# pylint: disable=missing-function-docstring, invalid-name


def test_O01(member):
    if (
        not member.license and not member.github
    ):  # probably too early, it is a new submission
        pytest.skip("too early, new submission")
    if member.license:
        assert len(str(member.license)) > 1
    elif member.github and hasattr(member.github, "license") and member.github.license:
        assert len(str(member.github.license)) > 1
    else:
        assert (
            False
        ), "No license could be found. Populate 'member.license' as soon as possible."
