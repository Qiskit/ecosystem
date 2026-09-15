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

from datetime import date
from unittest import TestCase
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO

from ecosystem.check import CheckData
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


class SourceBasedCheckupTestCase(TestCase):
    """A source-based check up is not the result of a test, so update_checkups keeps it"""

    def member_with_source_check(self):
        """A member with a passing checker and a source-based check up for the same ID"""
        member = Member(
            name="banana",
            url="https://github.com/BananaOrg/banana-repo",
            description="Banana short description.",
            checks={
                "014": CheckData(
                    "014",
                    since="2026-07-09",
                    source="https://github.com/BananaOrg/banana-repo/issues/1",
                    details="the description is not describing anything",
                )
            },
        )
        return member

    def test_source_checkup_survives(self):
        """The check up is not removed by a passing checker, and it keeps its own details"""
        member = self.member_with_source_check()
        with patch(
            "ecosystem.check.request_json",
            return_value={"state": "open", "state_reason": None},
        ), redirect_stdout(StringIO()):
            member.update_checkups("test_description.py::test_description_len_135")
        self.assertIn("014", member.checks)
        self.assertEqual(member.checks["014"].since, date(2026, 7, 9))
        self.assertEqual(
            member.checks["014"].details, "the description is not describing anything"
        )

    def test_closed_source_is_annotated(self):
        """A closed source issue is annotated in the details, but the check up stays"""
        member = self.member_with_source_check()
        with patch(
            "ecosystem.check.request_json",
            return_value={"state": "closed", "state_reason": "completed"},
        ), redirect_stdout(StringIO()):
            member.update_checkups("test_description.py::test_description_len_135")
        self.assertIn("014", member.checks)
        self.assertEqual(
            member.checks["014"].details,
            "the description is not describing anything "
            "(the source issue is closed as completed)",
        )
