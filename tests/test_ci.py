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

"""Tests for the CI commands, in ecosystem/cli/ci.py"""

import shutil
import tempfile
from contextlib import redirect_stdout
from datetime import date
from io import StringIO
from pathlib import Path
from unittest import TestCase
from unittest.mock import DEFAULT, patch

from ecosystem.check import CheckData
from ecosystem.cli import CliCI
from ecosystem.dao import DAO
from ecosystem.github import GitHubData
from ecosystem.member import Member


class CliCITestCase(TestCase):
    """A member in a temporary resources directory, the way a CI workflow sees one"""

    def setUp(self) -> None:
        self.path = Path(tempfile.mkdtemp())
        (self.path / "members").mkdir(parents=True, exist_ok=True)
        self.dao = DAO(self.path)

    def tearDown(self) -> None:
        shutil.rmtree(self.path)

    def add_member(self, **kwargs) -> Member:
        """A member passing every check up, plus whatever the test changes

        Passing is the baseline because each test here reads the output about one branch,
        and an unrelated failure would be another line in it.
        """
        kwargs.setdefault("interfaces", ["Python"])
        member = Member(
            name="Banana",
            url="https://github.com/banana-org/banana-repo",
            description="Compiles bananas into Qiskit circuits, over and over again, nicely.",
            license="Apache-2.0",
            maturity="experimental",
            labels=["optimization"],
            category="Tooling",
            **kwargs,
        )
        member.github = GitHubData(
            owner="banana-org",
            repo="banana-repo",
            stars=42,
            license="Apache-2.0",
            description="Compiles bananas",
            created_at=date(2020, 1, 1),
            last_commit=date.today(),
            last_activity=date.today(),
        )
        self.dao.write(member)
        return member

    def stored_file(self, member) -> str:
        """The member file as it is on disk"""
        return (self.path / "members" / f"{member.name_id}.toml").read_text()

    def run_command(self, command, *args, **kwargs):
        """Runs a command, returning its exit code (None unless it exits) and its output"""
        printed = StringIO()
        code = None
        try:
            with redirect_stdout(printed):
                command(*args, resources_dir=self.path, **kwargs)
        except SystemExit as exiting:
            code = exiting.code
        return code, printed.getvalue()

    def actions_lines(self, command, *args, **kwargs):
        """The same, with the output narrowed to the GitHub-Actions commands in it"""
        code, printed = self.run_command(command, *args, **kwargs)
        return code, [line for line in printed.splitlines() if line.startswith("::")]


class TestCreateSections(CliCITestCase):
    """`create_sections` unfolds the sections of a submitted member file, locally"""

    def test_the_github_section_comes_from_the_url(self):
        """It is what the submission issue gives, so it is where the section starts"""
        member = self.add_member()
        member.github = None
        self.dao.write(member)
        self.run_command(CliCI.create_sections)
        self.assertEqual("banana-org", self.dao[member.name_id].github.owner)
        self.assertEqual("banana-repo", self.dao[member.name_id].github.repo)

    def test_a_package_url_becomes_the_section_for_that_registry(self):
        """A submission lists its packages as URLs, one line each"""
        member = self.add_member(packages=["https://pypi.org/project/banana/"])
        self.run_command(CliCI.create_sections)
        stored = self.dao[member.name_id]
        self.assertIn("banana", stored.pypi)
        self.assertEqual([], stored.packages)

    def test_a_url_of_no_known_registry_stays_in_packages(self):
        """There is no section to unfold it into, and dropping it would lose it"""
        member = self.add_member(packages=["https://www.npmjs.com/package/banana"])
        self.run_command(CliCI.create_sections)
        self.assertEqual(
            ["https://www.npmjs.com/package/banana"],
            self.dao[member.name_id].packages,
        )

    def test_the_badge_section_is_created_with_no_url(self):
        """The url needs Bitly, so it is added when the submission is accepted"""
        member = self.add_member()
        self.run_command(CliCI.create_sections)
        self.assertIsNone(self.dao[member.name_id].badge.url)

    def test_only_the_member_asked_for_is_unfolded(self):
        """A submission PR runs this on the one member it adds"""
        other = self.add_member()
        member = self.add_member()
        for stored in (other, member):
            stored.github = None
            self.dao.write(stored)
        self.run_command(CliCI.create_sections, member.short_uuid)
        self.assertIsNotNone(self.dao[member.name_id].github)
        self.assertIsNone(self.dao[other.name_id].github)


class TestValidateMember(CliCITestCase):
    """`validate_member` runs the check ups and reports them as Actions annotations.

    The check ups read stored values only, so these run the real validation.
    """

    def test_a_member_passing_everything_is_a_notice(self):
        """And the command does not exit, which is what lets the PR merge"""
        member = self.add_member()
        code, lines = self.actions_lines(CliCI.validate_member, member.short_uuid)
        self.assertIsNone(code)
        self.assertEqual([f"::notice::  Banana ({member.name_id}) ✅"], lines)

    def test_an_explained_failure_is_grouped_under_the_notice(self):
        """The check up still fails; the explanation is why it is not a block"""
        member = self.add_member(interfaces=None)
        member.checks = {
            "007": CheckData(
                "007", since=date.today(), xfailed="bananas have no interface"
            )
        }
        self.dao.write(member)
        code, lines = self.actions_lines(CliCI.validate_member, member.short_uuid)
        self.assertIsNone(code)
        self.assertIn("::group:: some expected fail ☑️", lines)
        self.assertIn(
            "::notice:: checkup_classifications.py::checkup_007 - "
            "bananas have no interface️",
            lines,
        )
        self.assertEqual("::endgroup::", lines[-1])

    def test_a_failure_is_an_error_and_exits(self):
        """The exit code is what fails the workflow the command runs in"""
        member = self.add_member(interfaces=None)
        code, lines = self.actions_lines(CliCI.validate_member, member.short_uuid)
        self.assertEqual(1, code)
        self.assertIn(
            f"::error:: Banana ({member.name_id}) - "
            "checkup_classifications.py::checkup_007 failed ❌",
            lines,
        )

    def test_the_failure_report_is_a_collapsed_group(self):
        """It is the assertion message, which is long enough to fold away"""
        member = self.add_member(interfaces=None)
        _, lines = self.actions_lines(CliCI.validate_member, member.short_uuid)
        self.assertIn("member.interfaces", lines[1])
        self.assertTrue(lines[1].startswith("::group::"))
        self.assertEqual("::endgroup::", lines[2])

    def test_an_excluded_category_is_a_warning_instead(self):
        """A failure of a category the caller excluded is reported but not a block"""
        member = self.add_member(interfaces=None)
        code, lines = self.actions_lines(
            CliCI.validate_member, member.short_uuid, exclude="submission"
        )
        self.assertIsNone(code)
        self.assertEqual(
            [
                f"::warning:: Banana ({member.name_id}) - "
                "checkup_classifications.py::checkup_007 failed ❎️ (but not hard block) "
            ],
            lines,
        )

    def test_an_importance_can_be_excluded_too(self):
        """`[007]` is IMPORTANT, and the exclusions are read as either vocabulary"""
        member = self.add_member(interfaces=None)
        code, lines = self.actions_lines(
            CliCI.validate_member, member.short_uuid, exclude="important"
        )
        self.assertIsNone(code)
        self.assertIn("(but not hard block)", lines[0])

    def test_an_exclusion_that_does_not_apply_still_blocks(self):
        """Which is the point of naming them one by one"""
        member = self.add_member(interfaces=None)
        code, _ = self.actions_lines(
            CliCI.validate_member, member.short_uuid, exclude="activity"
        )
        self.assertEqual(1, code)


class TestUpdateMemberData(CliCITestCase):
    """`update_member_data` is the weekly fetch: one section at a time, per member"""

    FETCHES = ("github", "pypi", "crates", "cargo", "julia", "python", "requirements")

    def update(self, member_id=None, **behaviour):
        """Runs the command with every fetch stubbed out, so nothing reaches the network

        Returns the mocks, keyed as `update_<section>`, and the output.
        """
        stubs = {f"update_{section}": DEFAULT for section in self.FETCHES}
        stubs.update(behaviour)
        with patch.multiple(Member, **stubs) as fetches:
            _, printed = self.run_command(CliCI.update_member_data, member_id)
        return fetches, printed

    def test_every_section_is_fetched(self):
        """In the order the list has them: `python` reads what `github` stored"""
        self.add_member()
        fetches, printed = self.update()
        for section in self.FETCHES:
            with self.subTest(section=section):
                fetches[f"update_{section}"].assert_called_once_with()
        self.assertEqual(
            [f"Updating {section}️" for section in self.FETCHES],
            [line for line in printed.splitlines() if line.startswith("Updating")],
        )

    def test_the_member_is_a_group_of_its_own(self):
        """A run over the whole corpus is long, so the log folds per member"""
        member = self.add_member()
        _, printed = self.update()
        self.assertIn(f"::group:: Banana️ ({member.name_id})", printed)
        self.assertTrue(printed.rstrip().endswith("::endgroup::"))

    def test_what_a_fetch_found_is_written(self):
        """Each section is stored as it is fetched, not at the end of the member"""
        member = self.add_member()
        self.update(update_github=lambda self_: setattr(self_, "stars", 4242))
        self.assertIn("stars = 4242", self.stored_file(member))

    def test_an_alumni_member_is_skipped(self):
        """It is no longer a member, so nothing about it is refreshed"""
        self.add_member(status="Alumni")
        fetches, printed = self.update()
        self.assertIn("member.is_alumni, so skip", printed)
        fetches["update_github"].assert_not_called()

    def test_a_fetch_that_raises_is_a_warning_on_the_member_file(self):
        """One member failing cannot stop the run: there are 160 more after it"""
        member = self.add_member()
        fetches, printed = self.update(
            update_pypi=lambda _: (_ for _ in ()).throw(ValueError("no such package"))
        )
        self.assertIn(
            f"::warning file={self.path}/members/{member.name_id}.toml::Error updating "
            f"{member.name_id} when pypi️ - no such package",
            printed,
        )
        self.assertIn("ValueError: no such package", printed)
        fetches["update_julia"].assert_called_once_with()

    def test_only_the_member_asked_for_is_fetched(self):
        """The submission workflow updates the one member its PR adds"""
        member = self.add_member()
        other = self.add_member()
        _, printed = self.update(member.short_uuid)
        self.assertIn(member.name_id, printed)
        self.assertNotIn(other.name_id, printed)
