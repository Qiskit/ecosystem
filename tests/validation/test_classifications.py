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
"""Tests for ecosystem/validation/checkup_classifications.py"""

from unittest import TestCase
from contextlib import redirect_stdout
from io import StringIO

from ecosystem.member import Member


class ClassificationsTestCase(TestCase):
    """Tests for ecosystem/validation/checkup_classifications.py"""

    def test_invalid_category(self):
        """Invalid categories should fail validation check [008]."""
        member = Member(
            name="banana",
            url="https://github.com/BananaOrg/banana-repo",
            description="Banana description.",
            category="invalid category",
        )
        with redirect_stdout(StringIO()) as buffer:
            member.update_checkups("checkup_classifications.py::checkup_008")
        self.assertIn("FAILED", buffer.getvalue())
        self.assertIn("008", member.checks)

    def test_invalid_interfaces(self):
        """Invalid interfaces should fail validation check [007]."""
        member = Member(
            name="banana",
            url="https://github.com/BananaOrg/banana-repo",
            description="Banana description.",
            interfaces=["invalid interface"],
        )
        with redirect_stdout(StringIO()) as buffer:
            member.update_checkups("checkup_classifications.py::checkup_007")
        self.assertIn("FAILED", buffer.getvalue())
        self.assertIn("007", member.checks)

    def test_invalid_labels(self):
        """Invalid labels should fail validation check [009]."""
        member = Member(
            name="banana",
            url="https://github.com/BananaOrg/banana-repo",
            description="Banana description.",
            labels=["invalid label"],
        )
        with redirect_stdout(StringIO()) as buffer:
            member.update_checkups("checkup_classifications.py::checkup_009")
        self.assertIn("FAILED", buffer.getvalue())
        self.assertIn("009", member.checks)

    def test_invalid_maturity(self):
        """Invalid maturity values should fail validation check [004]."""
        member = Member(
            name="banana",
            url="https://github.com/BananaOrg/banana-repo",
            description="Banana description.",
            maturity="invalid maturity",
        )
        with redirect_stdout(StringIO()) as buffer:
            member.update_checkups("checkup_classifications.py::checkup_004")
        self.assertIn("FAILED", buffer.getvalue())
        self.assertIn("004", member.checks)
