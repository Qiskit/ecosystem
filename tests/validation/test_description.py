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

"""Tests for ecosystem/validation/test_description.py"""

from unittest import TestCase
from contextlib import redirect_stdout
from io import StringIO

from ecosystem.member import Member


class ClassificationsTestCase(TestCase):
    """Tests for ecosystem/validation/test_description.py"""

    def test_invalid_category(self):
        """Long description fail validation check [014]."""
        member = Member(
            name="banana",
            url="https://github.com/BananaOrg/banana-repo",
            description="Banana very long long long long long long"
            " long long long long long long long long long long"
            " long long long long long long long long long long"
            " long long long long long long long long long long"
            " long long long long long long long long long long description.",
        )
        with redirect_stdout(StringIO()) as buffer:
            member.update_checkups("test_description.py::test_description_len_135")
        self.assertIn("FAILED", buffer.getvalue())
        self.assertIn("014", member.checks)
