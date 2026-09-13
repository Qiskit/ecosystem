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

"""Tests for cli."""

import io
import os
import shutil
import tempfile
from datetime import date, timedelta
from unittest import TestCase, mock
from contextlib import redirect_stdout
from pathlib import Path

from dateutil.relativedelta import relativedelta

from ecosystem.check import CheckData
from ecosystem.cli import CliCI, CliMembers
from ecosystem.dao import DAO
from ecosystem.github import GitHubData
from ecosystem.member import Member


def get_community_repo() -> Member:
    """Return main mock repo."""
    return Member(
        name="mock-qiskit",
        url="https://github.com/MockQiskit/mock-qiskit",
        description="Mock description for repo",
        license="Apache 2.0",
        labels=["mock", "tests"],
        badge="https://qisk.it/e",
        maturity="production-ready",
    )


def mocked_get_request(*_args, **_kwargs):
    """For mocking a 200 response to a http request"""
    return type(
        "MockResponse",
        (object,),
        {
            "status_code": 200,
            "elapsed": 100,
            "ok": True,
            "created_at": None,
            "text": "<title>Qiskit Ecosystem:</title>",
        },
    )()


class TestCli(TestCase):
    """Test class for cli."""

    def setUp(self) -> None:
        self.path = Path(tempfile.mkdtemp())
        (self.path / "members").mkdir(parents=True, exist_ok=True)
        with open(self.path / "labels.json", "w") as file:
            file.write("{}")
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(f"{self.current_dir}/resources/issue.md", "r") as issue_body_file:
            self.issue_body = issue_body_file.read()
        with open(f"{self.current_dir}/resources/issue_2.md", "r") as issue_body_file:
            self.issue_body_2 = issue_body_file.read()
        with open(
            f"{self.current_dir}/resources/issue_skip.md", "r"
        ) as issue_body_file:
            self.issue_body_skip = issue_body_file.read()
        with open(
            f"{self.current_dir}/resources/issue_extra.md", "r"
        ) as issue_body_file:
            self.issue_body_extra = issue_body_file.read()

    def tearDown(self) -> None:
        shutil.rmtree(self.path)

    def test_add_member_from_issue(self):
        """Tests /resources/issue.md parsing function.
        Function: Cli
                -> parser_issue
        """

        # /resources/issue.md
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            CliCI.add_member_from_issue(self.issue_body, resources_dir=self.path)

        output_value = captured_output.getvalue().split("\n")
        self.assertEqual("SUBMISSION_NAME=Qiskit Banana Compiler", output_value[0])

        retrieved_repos = DAO(self.path).get_all()
        expected = {
            "name": "Qiskit Banana Compiler",
            "url": "https://github.com/somebody/banana-compiler",
            "description": "Compile bananas into Qiskit quantum circuits. "
            "Supports all modern devices, including Musa × paradisiaca.",
            "contact_info": "author@banana-compiler.org",
            "labels": ["error mitigation", "quantum information", "optimization"],
            "interfaces": ["Python"],
            "website": "https://banana-compiler.org",
            "documentation": "https://banana-compiler.org/documentation",
            "reference_paper": "https://arxiv.org/abs/5555.22222",
            "category": "circuit manipulation",
            "maturity": "production-ready",
            "packages": [
                "https://pypi.org/project/banana-compiler",
                "https://pypi.org/project/banana-compiler-hpc",
                "https://crates.io/crates/rusty-banana-compiler",
                "https://marketplace.visualstudio.com/items?itemName=banana-code-assistance",
            ],
        }
        self.assertEqual(len(retrieved_repos), 1)
        retrieved = list(retrieved_repos)[0].to_dict()
        self.assertIsInstance(retrieved.pop("uuid"), str)
        self.assertDictEqual(expected, retrieved)

    def test_add_member_from_issue_2(self):
        """Tests /resources/issue_2.md parsing function.
        Function: Cli
                -> parser_issue
        """

        # /resources/issue_2.md
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            CliCI.add_member_from_issue(self.issue_body_2, resources_dir=self.path)

        output_value = captured_output.getvalue().split("\n")
        self.assertEqual("SUBMISSION_NAME=Qiskit Banana Compiler", output_value[0])

        retrieved_repos = DAO(self.path).get_all()
        expected = {
            "name": "Qiskit Banana Compiler",
            "url": "https://github.com/somebody/banana-compiler",
            "description": "Compile bananas into Qiskit quantum circuits. "
            "Supports all modern devices, including Musa × paradisiaca.",
            "labels": [],
            "interfaces": ["Other"],
            "category": "circuit manipulation",
            "maturity": "production-ready",
            "packages": [],
        }
        self.assertEqual(len(retrieved_repos), 1)
        retrieved = list(retrieved_repos)[0].to_dict()
        self.assertIsInstance(retrieved.pop("uuid"), str)
        self.assertDictEqual(expected, retrieved)

    def test_add_member_from_issue_skip(self):
        """Tests /resources/issue_skip.md parsing function.
        An issue with skip checks
        """

        # /resources/issue_skip.md
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            CliCI.add_member_from_issue(self.issue_body_skip, resources_dir=self.path)

        output_value = captured_output.getvalue().split("\n")
        self.assertEqual("SUBMISSION_NAME=Qiskit Banana Compiler", output_value[0])

        retrieved_repos = DAO(self.path).get_all()
        expected = {
            "name": "Qiskit Banana Compiler",
            "url": "https://github.com/somebody/banana-compiler",
            "description": "Compile bananas into Qiskit quantum circuits. "
            "Supports all modern devices, including Musa × paradisiaca.",
            "labels": [],
            "interfaces": ["Python"],
            "category": "SDK",
            "maturity": "production-ready",
            "packages": [],
            "checks": {
                "010": {
                    "importance": "RECOMMENDATION",
                    "xfailed": 'This project is allow to have "test" in its name',
                },
                "COC": {
                    "importance": "CRITICAL",
                    "xfailed": "This project does not need to agree the CoC",
                },
            },
        }
        self.assertEqual(len(retrieved_repos), 1)
        retrieved = list(retrieved_repos)[0].to_dict()
        self.assertIsInstance(retrieved.pop("uuid"), str)
        self.assertDictEqual(expected, retrieved)

    def test_add_member_from_issue_extra(self):
        """Tests /resources/issue_extra.md parsing function.
        An issue with extra sections that can be ignored
        (like in https://github.com/Qiskit/ecosystem/issues/1123)
        """

        # /resources/issue_extra.md
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            CliCI.add_member_from_issue(self.issue_body_extra, resources_dir=self.path)

        output_value = captured_output.getvalue().split("\n")
        self.assertEqual("SUBMISSION_NAME=Qiskit Banana Compiler", output_value[0])

        retrieved_repos = DAO(self.path).get_all()
        expected = {
            "name": "Qiskit Banana Compiler",
            "url": "https://github.com/somebody/banana-compiler",
            "description": "Compile bananas into Qiskit quantum circuits. "
            "Supports all modern devices, including Musa × paradisiaca.",
            "labels": [],
            "interfaces": ["Python"],
            "category": "SDK",
            "maturity": "production-ready",
            "packages": [],
        }
        self.assertEqual(len(retrieved_repos), 1)
        retrieved = list(retrieved_repos)[0].to_dict()
        self.assertIsInstance(retrieved.pop("uuid"), str)
        self.assertDictEqual(expected, retrieved)

    @mock.patch("requests.get", new=mocked_get_request)
    def test_create_badge_endpoints(self):
        """Tests creating badges."""
        commu_success = get_community_repo()
        dao = DAO(self.path)

        # insert entry
        dao.write(commu_success)

        cli_members = CliMembers(root_path=os.path.join(self.current_dir, ".."))
        cli_members.resources_dir = self.path
        cli_members.current_dir = self.path
        cli_members.dao = dao

        # create badge endpoints
        cli_members.create_badge_endpoints()

        # gets a short url and updates the list in qisk.it/ecosystem-badges
        cli_members.update_badge_list()

        badges_folder_path = f"{cli_members.current_dir}/badges"
        self.assertTrue(
            os.path.isfile(f"{badges_folder_path}/{commu_success.short_uuid}")
        )

        # check version status
        with open(
            f"{badges_folder_path}/{commu_success.short_uuid}", "r"
        ) as json_blueviolet:
            json_success = json_blueviolet.read()
        self.assertTrue('"color": "6929C4"' in json_success)

        os.remove(f"{badges_folder_path}/{commu_success.short_uuid}")


class TestUpdateStatus(TestCase):
    """Tests for CliMembers.update_status"""

    def setUp(self) -> None:
        self.path = Path(tempfile.mkdtemp())
        (self.path / "members").mkdir(parents=True, exist_ok=True)
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.cli_members = CliMembers(root_path=os.path.join(self.current_dir, ".."))
        self.cli_members.resources_dir = self.path
        self.cli_members.current_dir = self.path
        self.cli_members.dao = DAO(self.path)

    def tearDown(self) -> None:
        shutil.rmtree(self.path)

    def add_member(
        self, months_old=None, maturity="production-ready", **kwargs
    ) -> Member:
        """Writes a member in the temporary DAO. If months_old is given,
        the GitHub repository was created that many months ago."""
        member = Member(
            name="mock-qiskit",
            url="https://github.com/MockQiskit/mock-qiskit",
            description="Mock description for repo",
            license="Apache 2.0",
            maturity=maturity,
            **kwargs,
        )
        if months_old is not None:
            member.github = GitHubData(
                owner="MockQiskit",
                repo="mock-qiskit",
                created_at=date.today() - relativedelta(months=months_old),
            )
        self.cli_members.dao.write(member)
        return member

    def status_after_update(self, **kwargs):
        """Adds a member, runs update_status, and returns the resulting status"""
        member = self.add_member(**kwargs)
        self.cli_members.update_status()
        return self.cli_members.dao[member.name_id].status

    def test_very_early_project(self):
        """A repository younger than 6 months is a "Very Early Project" """
        self.assertEqual(self.status_after_update(months_old=2), "Very Early Project")

    def test_early_project(self):
        """A repository between 6 and 18 months old is an "Early Project" """
        self.assertEqual(self.status_after_update(months_old=10), "Early Project")

    def test_six_months_old_is_early_project(self):
        """The "Very Early Project" status ends at 6 months"""
        self.assertEqual(self.status_after_update(months_old=6), "Early Project")

    def test_old_project_has_no_age_status(self):
        """A repository older than 18 months is a regular member (status None)"""
        self.assertIsNone(self.status_after_update(months_old=18))

    def test_no_created_at(self):
        """Without member.github.created_at there is no age-derived status"""
        self.assertIsNone(self.status_after_update())

    def test_age_status_is_recomputed(self):
        """An outdated age-derived status is removed"""
        self.assertIsNone(
            self.status_after_update(months_old=30, status="Very Early Project")
        )

    def test_unmaintained(self):
        """An `as-is` project is "Unmaintained" """
        self.assertEqual(self.status_after_update(maturity="as-is"), "Unmaintained")

    def test_deprecated_is_unmaintained(self):
        """A `deprecated` project is "Unmaintained" too"""
        self.assertEqual(
            self.status_after_update(maturity="deprecated"), "Unmaintained"
        )

    def test_unmaintained_takes_precedence_over_age(self):
        """`as-is` is a stronger signal than the age of the repository"""
        self.assertEqual(
            self.status_after_update(months_old=2, maturity="as-is"), "Unmaintained"
        )

    def test_unmaintained_is_recomputed(self):
        """An outdated "Unmaintained" status is removed"""
        self.assertIsNone(self.status_after_update(status="Unmaintained"))

    def test_qiskit_project_is_not_updated(self):
        """ "Qiskit Project" is governed differently, so it is not age-derived"""
        self.assertEqual(
            self.status_after_update(months_old=2, status="Qiskit Project"),
            "Qiskit Project",
        )

    def test_alumni_is_not_updated(self):
        """Alumni projects stay alumni, no matter how young they are"""
        self.assertEqual(
            self.status_after_update(months_old=2, status="Alumni"), "Alumni"
        )

    def test_no_alumni_postpones_the_retirement(self):
        """With no_alumni, an expired cure period keeps the project "Under revision" """
        member = self.add_member()
        member.checks = {
            "001": CheckData("001", since=date.today() - timedelta(days=1))
        }
        self.cli_members.dao.write(member)
        self.cli_members.update_status(no_alumni=True)
        self.assertEqual(
            self.cli_members.dao[member.name_id].status,
            "Under revision",
        )

    def test_expired_cure_period_is_alumni(self):
        """Without no_alumni, an expired cure period moves the project to "Alumni" """
        member = self.add_member()
        member.checks = {
            "001": CheckData("001", since=date.today() - timedelta(days=1))
        }
        self.cli_members.dao.write(member)
        self.cli_members.update_status()
        self.assertEqual(self.cli_members.dao[member.name_id].status, "Alumni")

    def test_under_revision_takes_precedence(self):
        """A pending check up is more important than the age of the repository"""
        member = self.add_member(months_old=2)
        member.checks = {"001": CheckData("001", since=date.today())}
        self.cli_members.dao.write(member)
        self.cli_members.update_status()
        self.assertEqual(
            self.cli_members.dao[member.name_id].status,
            "Under revision",
        )

    def test_early_projects_share_one_table(self):
        """Both early statuses are listed in a single docs/assets/early-projects.md table"""
        self.add_member(months_old=2)
        self.add_member(months_old=10)
        self.add_member(months_old=30)
        self.cli_members.update_status()

        # pylint: disable=protected-access
        projects = self.cli_members._all_projects_classifications("status")["status"]
        self.cli_members.update_assets_status(projects)

        table = (self.path / "docs" / "assets" / "early-projects.md").read_text()
        self.assertIn("There are 2 projects with these statuses", table)
        self.assertIn("| Project | Status | Repository created | Age (months) |", table)
        # youngest project first
        statuses = [
            line.split("|")[2].strip()
            for line in table.splitlines()
            if line.strip().startswith("| [")
        ]
        self.assertEqual(statuses, ["Very Early Project", "Early Project"])
        self.assertFalse((self.path / "docs" / "assets" / "early-project.md").exists())
