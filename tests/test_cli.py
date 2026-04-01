"""Tests for cli."""

import io
import os
import shutil
import tempfile
from unittest import TestCase, mock
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
        badge="https://qisk.it/e",
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
            "text": "",
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
            "website": "https://banana-compiler.org",
            "documentation": "https://banana-compiler.org/documentation",
            "reference_paper": "https://arxiv.org/abs/5555.22222",
            "group": "circuit manipulation",
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
            "group": "circuit manipulation",
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
            "group": "circuit manipulation",
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

    @mock.patch("requests.get", new=mocked_get_request)
    def test_update_badges(self):
        """Tests creating badges."""
        commu_success = get_community_repo()
        dao = DAO(self.path)

        # insert entry
        dao.write(commu_success)

        cli_members = CliMembers(root_path=os.path.join(self.current_dir, ".."))
        cli_members.resources_dir = self.path
        cli_members.current_dir = self.path
        cli_members.dao = dao

        # create badges
        cli_members.update_badges()

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
