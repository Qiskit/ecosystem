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
"""Tests for ecosystem/validation/checkup_github.py"""

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
    """Shared setup for the ecosystem/validation/checkup_github.py check ups"""

    @staticmethod
    def member(
        status,
        months_old=60,
        months_since_commit=1,
        archived=False,
        topics=None,
        github_description="Banana repository description.",
        **kwargs,
    ):
        """A member with a GitHub repository of the given age and activity.

        A falsy `archived`, `topics` or `github_description` builds no entry at all, which
        is how a repository that is neither archived nor tagged nor described looks in a
        member file. Passing the key with a `None` value would leave it out of `to_dict`
        just the same, but `hasattr(member.github, ...)` would be true, and a check up
        written in the `[G09]` style reads exactly that.

        `github_description` is the repository's own description, not
        `member.description`."""
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
            created_at=date.today() - relativedelta(months=months_old),
            last_commit=date.today() - relativedelta(months=months_since_commit),
            last_activity=date.today() - relativedelta(months=months_since_commit),
            **({"archived": True} if archived else {}),
            **({"topics": topics} if topics else {}),
            **({"description": github_description} if github_description else {}),
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
        return {id_: records[0].details for id_, records in member.checks.items()}

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
        checker = "checkup_github.py::checkup_G05"
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
        checker = "checkup_github.py::checkup_G07"
        self.assert_same_for_every_status(
            checker, set(), months_since_commit=24, maturity="as-is"
        )
        self.assert_same_for_every_status(
            checker, {"G07"}, months_since_commit=24, maturity="production-ready"
        )

    def test_G08_asks_for_the_repository_to_be_archived(self):
        """The other direction: declaring no maintenance asks for an archived repository"""
        checker = "checkup_github.py::checkup_G08"
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
                "checkup_github.py::checkup_G08",
                status=None,
                maturity="as-is",
                archived=None,
            ),
            {"G08": "Unmaintained project should have an archived GitHub repository"},
        )

    def test_G11_asks_for_the_repository_to_be_archived(self):
        """Same as [G08], on an IBM-controlled organization"""
        checker = "checkup_github.py::checkup_G11"
        self.assert_same_for_every_status(checker, {"G11"}, maturity="deprecated")
        self.assert_same_for_every_status(checker, set(), maturity="production-ready")


class TestAgeGatedCheckups(GitHubCheckupsTestCase):
    """[G12] applies to young repositories, which is `member.age_in_months`,
    not the `(Very) Early Project` statuses derived from it."""

    def test_G12_uses_the_age_of_the_repository(self):
        """A 6-month-old repository with no commit in 5 months is decelerating"""
        checker = "checkup_github.py::checkup_G12"
        self.assert_same_for_every_status(
            checker, {"G12"}, months_old=6, months_since_commit=5
        )

    def test_G12_applies_to_a_young_project_that_went_quiet(self):
        """A worse deceleration cannot be exempt: the window is `max(2, age * 2/3)`,
        so 9 months without a commit at 6 months old is further past it, not nearer"""
        self.assert_same_for_every_status(
            "checkup_github.py::checkup_G12",
            {"G12"},
            months_old=6,
            months_since_commit=9,
        )

    def test_G12_does_not_apply_to_an_old_repository(self):
        """Older repositories are covered by the flat window of [G07] instead"""
        self.assert_same_for_every_status(
            "checkup_github.py::checkup_G12",
            set(),
            months_old=60,
            months_since_commit=24,
        )


class TestTopicsReachTheMember(GitHubCheckupsTestCase):
    """The repository topics are on the member, ready for a check up to read.

    No check up asserts on them yet, so this covers the plumbing `update_github` fills in:
    a topic list that reaches a member file is a topic list a checker can be written
    against, and an empty one has to be absent rather than falsy-but-present."""

    def test_topics_are_on_the_member(self):
        """A member built with topics carries them on its GitHub section"""
        member = self.member(None, topics=["qiskit", "quantum-computing"])
        self.assertEqual(member.github.topics, ["qiskit", "quantum-computing"])

    def test_no_topics_leaves_the_entry_out(self):
        """A repository with no topic has no entry at all, the way `archived` does.

        `to_dict` alone does not say so: a section built with `topics=None` leaves the key
        out of it either way, and only `hasattr` tells that fixture apart from a member
        file that never had the key."""
        github = self.member(None).github
        self.assertNotIn("topics", github.to_dict())
        self.assertFalse(hasattr(github, "topics"))

    def test_the_fixture_matches_a_member_file_with_no_topics(self):
        """The section a member file with no `topics` builds, which is the real shape.

        The fixture used to pass `topics=None` unconditionally, so `hasattr` was true
        where a real member's is false. A check up asserting `hasattr(github, "topics")`
        would have passed here and failed in production, which is the way round that
        hides a bug."""
        from_file = GitHubData.from_dict(
            {"owner": "qiskit-community", "repo": "banana"}
        )
        self.assertEqual(
            hasattr(self.member(None).github, "topics"), hasattr(from_file, "topics")
        )


class TestG14(GitHubCheckupsTestCase):
    """[G14] Have `qiskit` among the GitHub repository topics"""

    CHECKER = "checkup_github.py::checkup_G14"

    def test_G14_reads_the_topic_list(self):
        """A repository passes when `qiskit` is one of its topics, whatever else is"""
        self.assert_same_for_every_status(
            self.CHECKER, set(), topics=["qiskit", "python"]
        )
        self.assert_same_for_every_status(
            self.CHECKER, {"G14"}, topics=["quantum-computing"]
        )

    def test_G14_wants_the_topic_itself_not_a_prefix_of_it(self):
        """`qiskit-addon` is a different topic, and not on the `qiskit` page.

        Two repositories in the corpus carry it and not `qiskit`, so this is the case that
        decides whether the check up reads the list or a prefix of it."""
        self.assert_same_for_every_status(
            self.CHECKER, {"G14"}, topics=["qiskit-addon"]
        )

    def test_G14_says_nothing_about_a_repository_with_no_topics(self):
        """No topic at all is a section that may simply predate `topics` being recorded.

        It reads the same as a repository that declares none, so reporting it would report
        this project's own data gap as the member's."""
        self.assert_same_for_every_status(self.CHECKER, set())

    def test_G14_exempts_declared_unmaintained(self):
        """A project with no maintenance expectations owes no retagging"""
        self.assert_same_for_every_status(
            self.CHECKER, set(), maturity="as-is", topics=["quantum-computing"]
        )
        self.assert_same_for_every_status(
            self.CHECKER, set(), maturity="deprecated", topics=["quantum-computing"]
        )
        self.assert_same_for_every_status(
            self.CHECKER,
            {"G14"},
            maturity="production-ready",
            topics=["quantum-computing"],
        )

    def test_G14_reports_where_the_repository_is_missing_from(self):
        """The details name the page the repository does not show up on"""
        details = self.details_of(
            self.CHECKER, status=None, topics=["quantum-computing"]
        )
        self.assertIn("github.com/topics/qiskit", details["G14"])


class TestG15(GitHubCheckupsTestCase):
    """[G15] Have a description on the GitHub repository"""

    CHECKER = "checkup_github.py::checkup_G15"

    def test_G15_reads_the_repositorys_own_description(self):
        """A repository that introduces itself passes"""
        self.assert_same_for_every_status(
            self.CHECKER, set(), github_description="A compiler for bananas."
        )

    def test_G15_covers_every_way_of_having_none(self):
        """`null`, the empty string and whitespace all mean the same thing.

        GitHub answers `null` for a repository with no description, so the attribute is
        there holding None, and it stores an empty string as it comes."""
        for empty in [None, "", "   "]:
            with self.subTest(description=empty):
                self.assert_same_for_every_status(
                    self.CHECKER, {"G15"}, github_description=empty
                )

    def test_G15_exempts_declared_unmaintained(self):
        """A project with no maintenance expectations owes no description"""
        self.assert_same_for_every_status(
            self.CHECKER, set(), maturity="as-is", github_description=None
        )
        self.assert_same_for_every_status(
            self.CHECKER, set(), maturity="deprecated", github_description=None
        )
        self.assert_same_for_every_status(
            self.CHECKER, {"G15"}, maturity="production-ready", github_description=None
        )

    def test_G15_is_not_about_the_submitted_description(self):
        """`member.description` is a different field, which [014] checks.

        The member always has one, so a repository with none has to fail even though the
        catalog has a sentence to show."""
        member = self.member(None, github_description=None)
        self.assertTrue(member.description)
        self.assertEqual(
            self.checkups_of(self.CHECKER, status=None, github_description=None),
            {"G15"},
        )

    def test_G15_reports_what_is_missing(self):
        """The details name the repository's own line, not the member's"""
        details = self.details_of(self.CHECKER, status=None, github_description=None)
        self.assertIn("no description", details["G15"])
