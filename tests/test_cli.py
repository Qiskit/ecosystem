"""Tests for cli."""
import os
import io
from unittest import TestCase
from contextlib import redirect_stdout

from ecosystem.cli import CliCI, CliWebsite, CliMembers
from ecosystem.daos import DAO
from ecosystem.models import Tier
from ecosystem.models.repository import Repository


def get_community_repo() -> Repository:
    """Return main mock repo."""
    return Repository(
        name="mock-qiskit-terra",
        url="https://github.com/MockQiskit/mock-qiskit-wsdt.terra",
        description="Mock description for repo. wsdt",
        licence="Apache 2.0",
        labels=["mock", "tests", "wsdt"],
        tier=Tier.COMMUNITY,
    )


class TestCli(TestCase):
    """Test class for cli."""

    def setUp(self) -> None:
        self.path = "../resources"
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(
            "{}/resources/issue.md".format(self.current_dir), "r"
        ) as issue_body_file:
            self.issue_body = issue_body_file.read()
        with open(
            "{}/resources/issue_2.md".format(self.current_dir), "r"
        ) as issue_body_file:
            self.issue_body_2 = issue_body_file.read()

    def test_build_website(self):
        """Test the website builder function."""
        cli_website = CliWebsite(root_path=f"{os.path.abspath(os.getcwd())}/../")
        self.assertIsInstance(cli_website.build_website(), str)

    def test_parser_issue(self):
        """Tests issue parsing function.
        Function: Cli
                -> parser_issue
        Args:
            issue_body
        """

        # Issue 1
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            CliCI.parser_issue(self.issue_body)

        output_value = captured_output.getvalue().split("\n")

        self.assertEqual(output_value[0], "SUBMISSION_NAME=awesome")
        self.assertEqual(
            output_value[1],
            "SUBMISSION_REPO=http://github.com/awesome/awesome",
        )
        self.assertEqual(
            output_value[2],
            "SUBMISSION_DESCRIPTION=An awesome repo for awesome project multiple"
            " paragraphs",
        )
        self.assertEqual(output_value[3], "SUBMISSION_LICENCE=Apache License 2.0")
        self.assertEqual(output_value[4], "SUBMISSION_CONTACT=toto@gege.com")
        self.assertEqual(output_value[5], "SUBMISSION_ALTERNATIVES=tititata")
        self.assertEqual(output_value[6], "SUBMISSION_AFFILIATIONS=_No response_")
        self.assertEqual(
            output_value[7],
            "SUBMISSION_LABELS=['tool', 'tutorial', 'paper implementation']",
        )
        self.assertEqual(
            output_value[8],
            "SUBMISSION_WEBSITE=https://qiskit.org/ecosystem/",
        )

        # Issue 2
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            CliCI.parser_issue(self.issue_body_2)

        output_value = captured_output.getvalue().split("\n")

        self.assertEqual(output_value[0], "SUBMISSION_NAME=awesome")
        self.assertEqual(
            output_value[1],
            "SUBMISSION_REPO=http://github.com/awesome/awesome",
        )
        self.assertEqual(
            output_value[2],
            "SUBMISSION_DESCRIPTION=An awesome repo for awesome project",
        )
        self.assertEqual(output_value[3], "SUBMISSION_LICENCE=Apache License 2.0")
        self.assertEqual(output_value[4], "SUBMISSION_CONTACT=toto@gege.com")
        self.assertEqual(output_value[5], "SUBMISSION_ALTERNATIVES=_No response_")
        self.assertEqual(output_value[6], "SUBMISSION_AFFILIATIONS=Awesome Inc.")
        self.assertEqual(
            output_value[7],
            "SUBMISSION_LABELS=[]",
        )
        self.assertEqual(
            output_value[8],
            "SUBMISSION_WEBSITE=None",
        )

    def test_update_badges(self):
        """Tests creating badges."""
        commu_success = get_community_repo()
        dao = DAO(self.path)

        # insert entry
        dao.write(commu_success)

        cli_members = CliMembers(root_path=os.path.join(self.current_dir, ".."))
        cli_members.resources_dir = "../resources"
        cli_members.dao = dao

        # create badges
        cli_members.update_badges()

        badges_folder_path = "{}/badges".format(cli_members.current_dir)
        self.assertTrue(
            os.path.isfile(f"{badges_folder_path}/{commu_success.name}.svg")
        )

        # check version status
        with open(
            f"{badges_folder_path}/{commu_success.name}.svg", "r"
        ) as svg_blueviolet:
            svg_success = svg_blueviolet.read()
        self.assertTrue('fill="blueviolet"' in svg_success)

        os.remove(f"{badges_folder_path}/{commu_success.name}.svg")
