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
"""Tests for ecosystem/validation/test_github.py"""

# the test methods are named after the check up they cover, like [G05]
# pylint: disable=invalid-name

from contextlib import redirect_stdout
from datetime import date
from io import StringIO
from unittest import TestCase

from dateutil.relativedelta import relativedelta

from ecosystem.github import GitHubData
from ecosystem.member import Member

# `member.status` is a derived value that `Under revision` masks as soon as any check up is
# pending. A check up that gated on it would flip on and off on every run, so these are the
# statuses each check up below has to be blind to.
EVERY_STATUS = [None, "Member", "Unmaintained", "Under revision", "Early Project"]


class GitHubCheckupsTestCase(TestCase):
    """Shared setup for the ecosystem/validation/test_github.py check ups"""

    @staticmethod
    def member(status, months_old=60, months_since_commit=1, archived=False, **kwargs):
        """A member with a GitHub repository of the given age and activity.

        `archived=None` leaves the entry out altogether, which is how a repository that is
        not archived looks in a member file (see `GitHubData.json_types`)."""
        member = Member(
            name="banana",
            url="https://github.com/qiskit-community/banana-repo",
            description="Banana description.",
            license="Apache-2.0",
            status=status,
            **kwargs,
        )
        member.github = GitHubData(
            owner="qiskit-community",
            repo="banana-repo",
            archived=archived or None,
            created_at=date.today() - relativedelta(months=months_old),
            last_commit=date.today() - relativedelta(months=months_since_commit),
            last_activity=date.today() - relativedelta(months=months_since_commit),
        )
        return member

    def checkups_of(self, checker, **member_kwargs):
        """The ids of the check ups that `checker` records on such a member"""
        member = self.member(**member_kwargs)
        with redirect_stdout(StringIO()):
            member.update_checkups(checker)
        return set(member.checks)

    def details_of(self, checker, **member_kwargs):
        """The details each check up that `checker` records on such a member reports"""
        member = self.member(**member_kwargs)
        with redirect_stdout(StringIO()):
            member.update_checkups(checker)
        return {id_: checkup.details for id_, checkup in member.checks.items()}

    def assert_same_for_every_status(self, checker, expected, **member_kwargs):
        """The check up records `expected` whatever `member.status` says"""
        for status in EVERY_STATUS:
            with self.subTest(status=status):
                self.assertEqual(
                    self.checkups_of(checker, status=status, **member_kwargs),
                    expected,
                    msg=f"the outcome of {checker} depends on member.status",
                )


class TestMaturityGatedCheckups(GitHubCheckupsTestCase):
    """[G05], [G07], [G08] and [G11] ask whether the project is maintained, which is
    `member.maturity`, not the `Unmaintained` status derived from it."""

    def test_G05_exempts_as_is_only(self):
        """An archived repository is fine only once the project declares itself `as-is`.

        `deprecated` is not enough: the project is still offered for use, so an archived
        repository is a check up even though `Member.unmaintained` is true."""
        checker = "test_github.py::test_G05"
        self.assert_same_for_every_status(
            checker, set(), archived=True, maturity="as-is"
        )
        self.assert_same_for_every_status(
            checker, {"G05"}, archived=True, maturity="deprecated"
        )
        self.assert_same_for_every_status(
            checker, {"G05"}, archived=True, maturity="production-ready"
        )

    def test_G07_exempts_declared_unmaintained(self):
        """A project with no maintenance expectations owes no commits"""
        checker = "test_github.py::test_G07"
        self.assert_same_for_every_status(
            checker, set(), months_since_commit=24, maturity="as-is"
        )
        self.assert_same_for_every_status(
            checker, {"G07"}, months_since_commit=24, maturity="production-ready"
        )

    def test_G08_asks_for_the_repository_to_be_archived(self):
        """The other direction: declaring no maintenance asks for an archived repository"""
        checker = "test_github.py::test_G08"
        self.assert_same_for_every_status(checker, {"G08"}, maturity="as-is")
        self.assert_same_for_every_status(
            checker, set(), maturity="as-is", archived=True
        )
        self.assert_same_for_every_status(checker, set(), maturity="production-ready")

    def test_G08_without_an_archived_entry(self):
        """A repository that is not archived has no `github.archived` entry at all, and the
        check up has to report what is wrong instead of how it found out"""
        self.assertEqual(
            self.details_of(
                "test_github.py::test_G08",
                status=None,
                maturity="as-is",
                archived=None,
            ),
            {"G08": "Unmaintained project should have an archived GitHub repository"},
        )

    def test_G11_asks_for_the_repository_to_be_archived(self):
        """Same as [G08], on an IBM-controlled organization"""
        checker = "test_github.py::test_G11"
        self.assert_same_for_every_status(checker, {"G11"}, maturity="deprecated")
        self.assert_same_for_every_status(checker, set(), maturity="production-ready")


class TestAgeGatedCheckups(GitHubCheckupsTestCase):
    """[G12] applies to young repositories, which is `member.age_in_months`,
    not the `(Very) Early Project` statuses derived from it."""

    def test_G12_uses_the_age_of_the_repository(self):
        """A 6-month-old repository with no commit in 5 months is decelerating"""
        checker = "test_github.py::test_G12"
        self.assert_same_for_every_status(
            checker, {"G12"}, months_old=6, months_since_commit=5
        )

    def test_G12_does_not_apply_to_an_old_repository(self):
        """Older repositories are covered by the flat window of [G07] instead"""
        self.assert_same_for_every_status(
            "test_github.py::test_G12", set(), months_old=60, months_since_commit=24
        )
