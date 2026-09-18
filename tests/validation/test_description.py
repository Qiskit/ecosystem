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

from datetime import date, timedelta
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


class XfailedExpirationTestCase(TestCase):
    """An xfail explanation stops applying once check.xfailed_until has passed"""

    reason = "the front-end of this project can deal with long descriptions"

    def member_with_xfail(self, xfailed_until=None, **check_kwargs):
        """A member failing check up 014 with an explanation for it"""
        return Member(
            name="banana",
            url="https://github.com/BananaOrg/banana-repo",
            description="Banana very long long long long long long"
            " long long long long long long long long long long"
            " long long long long long long long long long long"
            " long long long long long long long long long long"
            " long long long long long long long long long long description.",
            checks={
                "014": CheckData(
                    "014",
                    xfailed=self.reason,
                    xfailed_until=xfailed_until,
                    **check_kwargs,
                )
            },
        )

    def update(self, member):
        """Runs the 014 checker on the member"""
        with redirect_stdout(StringIO()) as buffer:
            member.update_checkups("test_description.py::test_description_len_135")
        return buffer.getvalue()

    def test_valid_explanation_is_kept(self):
        """While the explanation is valid, the check up is expected to fail
        and the expiration date survives the update"""
        expires = date.today() + timedelta(days=30)
        member = self.member_with_xfail(expires)
        output = self.update(member)
        self.assertIn("XFAIL", output)
        self.assertEqual(member.checks["014"].xfailed, self.reason)
        self.assertEqual(member.checks["014"].xfailed_until, expires)

    def test_explanation_without_expiration_is_kept(self):
        """An explanation without an expiration date keeps working as before"""
        member = self.member_with_xfail()
        output = self.update(member)
        self.assertIn("XFAIL", output)
        self.assertEqual(member.checks["014"].xfailed, self.reason)
        self.assertIsNone(member.checks["014"].xfailed_until)

    def test_expired_explanation_is_dropped(self):
        """Once the explanation expired, the check up fails as a regular one and the
        cure period starts today"""
        member = self.member_with_xfail(date.today() - timedelta(days=1))
        output = self.update(member)
        self.assertIn("FAILED", output)
        self.assertIn("014", member.checks)
        self.assertIsNone(member.checks["014"].xfailed)
        self.assertIsNone(member.checks["014"].xfailed_until)
        self.assertEqual(member.checks["014"].since, date.today())

    def test_expired_explanation_on_a_passing_checkup(self):
        """An expired explanation on a check up that passes removes the check up"""
        member = self.member_with_xfail(date.today() - timedelta(days=1))
        member.description = "Banana short description."
        self.update(member)
        self.assertNotIn("014", member.checks)

    def test_checkup_without_checker_does_not_break_the_collection(self):
        """A check up that has no checker (so it can only be source-based) cannot be
        translated into an xfail mark, and it does not block the ones that can"""
        member = self.member_with_xfail()
        member.checks["COC"] = CheckData("COC", xfailed="no CoC needed")
        output = self.update(member)
        self.assertIn("XFAIL", output)
        self.assertEqual(member.checks["014"].xfailed, self.reason)


class SourceBasedXfailExpirationTestCase(TestCase):
    """A source-based check up does not come from a test,
    so its expired explanation is dropped explicitly"""

    reason = "the maintainer asked for extra time"
    issue = "https://github.com/BananaOrg/banana-repo/issues/1"

    def member_with_source_xfail(self, xfailed_until):
        """A member with a source-based check up that is excused until `xfailed_until`"""
        return Member(
            name="banana",
            url="https://github.com/BananaOrg/banana-repo",
            description="Banana short description.",
            checks={
                "014": CheckData(
                    "014",
                    since="2026-07-09",
                    source=self.issue,
                    details="the description is not describing anything",
                    xfailed=self.reason,
                    xfailed_until=xfailed_until,
                )
            },
        )

    def update(self, member):
        """Runs the 014 checker on the member, with an open source issue"""
        with patch(
            "ecosystem.check.request_json",
            return_value={"state": "open", "state_reason": None},
        ), redirect_stdout(StringIO()):
            member.update_checkups("test_description.py::test_description_len_135")

    def test_valid_explanation_is_kept(self):
        """While the explanation is valid, it stays on the source-based check up"""
        expires = date.today() + timedelta(days=30)
        member = self.member_with_source_xfail(expires)
        self.update(member)
        self.assertEqual(member.checks["014"].xfailed, self.reason)
        self.assertEqual(member.checks["014"].xfailed_until, expires)
        self.assertEqual(member.checks["014"].since, date(2026, 7, 9))

    def test_expired_explanation_is_dropped(self):
        """An expired explanation is removed, so the check up counts again.
        The source, the details, and the original `since` are untouched"""
        member = self.member_with_source_xfail(date.today() - timedelta(days=1))
        self.update(member)
        self.assertIn("014", member.checks)
        self.assertIsNone(member.checks["014"].xfailed)
        self.assertIsNone(member.checks["014"].xfailed_until)
        self.assertEqual(member.checks["014"].source, self.issue)
        self.assertEqual(member.checks["014"].since, date(2026, 7, 9))
