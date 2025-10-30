"""Tests for cli."""

import io
import os
import shutil
import tempfile
from unittest import TestCase
from contextlib import redirect_stdout
from pathlib import Path

from ecosystem.cli import CliCI, CliMembers
from ecosystem.dao import DAO
from ecosystem.member import Member


def get_community_repo() -> Member:
    """Return main mock repo."""
    return Member(
        name="mock-qiskit-terra",
        url="https://github.com/MockQiskit/mock-qiskit-wsdt.terra",
        description="Mock description for repo. wsdt",
        licence="Apache 2.0",
        labels=["mock", "tests", "wsdt"],
    )


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

    def tearDown(self) -> None:
        shutil.rmtree(self.path)

    def test_add_member_from_issue(self):
        # TODO, split parsing issue1 and issue2 in two different tests
        """Tests issue parsing function.
        Function: Cli
                -> parser_issue
        Args:
            issue_body
        """

        # Issue 1
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
            "ibm_maintained": False,
            "labels": ["error mitigation, quantum information, optimization"],
            "website": "https://banana-compiler.org",
            "documentation": "https://banana-compiler.org/documentation",
            "reference_paper": "https://arxiv.org/abs/5555.22222",
            "github": {"owner": "somebody", "repo": "banana-compiler"},
            "group": "circuit manipulation",
        }
        self.assertEqual(len(retrieved_repos), 1)
        retrieved = list(retrieved_repos)[0].to_dict()
        self.assertIsInstance(retrieved.pop("uuid"), str)
        badge_md = retrieved.pop("badge")
        self.assertIsInstance(badge_md, str)
        self.assertTrue(
            badge_md.startswith(
                "[![Qiskit Ecosystem](https://img.shields.io/"
                "endpoint?style=flat&url=https"
            )
        )
        self.assertTrue(badge_md.endswith("(https://qisk.it/e)"))
        self.assertEqual(expected, retrieved)

        # # Issue 2
        # captured_output = io.StringIO()
        # with redirect_stdout(captured_output):
        #     CliCI.add_member_from_issue(self.issue_body_2, resources_dir=self.path)
        #
        # output_value = captured_output.getvalue().split("\n")
        # self.assertEqual(output_value[0], "SUBMISSION_NAME=My awesome project")
        #
        # retrieved_repos = DAO(self.path).get_all()
        # expected = {
        #     "name": "My awesome project",
        #     "url": "http://github.com/awesome/awesome",
        #     "description": "An awesome repo for awesome project",
        #     "contact_info": "toto@gege.com",
        #     "licence": "Apache License 2.0",
        #     "affiliations": "Awesome Inc.",
        #     "ibm_maintained": False,
        #     "labels": [],
        #     "github": {"owner": "awesome", "repo": "awesome"},
        # }
        # self.assertEqual(len(retrieved_repos), 1)
        # retrieved = list(retrieved_repos)[0].to_dict()
        # self.assertIsInstance(retrieved.pop("uuid"), str)
        # badge_md = retrieved.pop("badge")
        # self.assertIsInstance(badge_md, str)
        # self.assertTrue(
        #     badge_md.startswith(
        #         "[![Qiskit Ecosystem](https://img.shields.io/"
        #         "endpoint?style=flat&url=https"
        #     )
        # )
        # self.assertTrue(badge_md.endswith("(https://qisk.it/e)"))
        # self.assertEqual(retrieved, expected)

    def test_update_badges(self):
        """Tests creating badges."""
        commu_success = get_community_repo()
        dao = DAO(self.path)

        # insert entry
        dao.write(commu_success)

        cli_members = CliMembers(root_path=os.path.join(self.current_dir, ".."))
        cli_members.resources_dir = self.path
        cli_members.dao = dao

        # create badges
        cli_members.update_badges()

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
