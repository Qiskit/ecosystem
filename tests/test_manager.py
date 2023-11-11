"""Tests for manager cli."""
import os
import io
from unittest import TestCase
from contextlib import redirect_stdout

import responses

from ecosystem.daos import DAO
from ecosystem.manager import Manager
from ecosystem.models import TestResult, Tier, TestType
from ecosystem.models.repository import Repository
from ecosystem.models.test_results import Package


def get_community_repo() -> Repository:
    """Return main mock repo."""
    return Repository(
        name="mock-qiskit-terra-with-success-dev-test",
        url="https://github.com/MockQiskit/mock-qiskit-wsdt.terra",
        description="Mock description for repo. wsdt",
        licence="Apache 2.0",
        labels=["mock", "tests", "wsdt"],
        tests_results=[
            TestResult(
                passed=True,
                test_type=TestType.DEV_COMPATIBLE,
                package=Package.QISKIT,
                package_version="0.18.0",
            ),
            TestResult(
                passed=True,
                test_type=TestType.STANDARD,
                package=Package.QISKIT,
                package_version="0.18.0",
            ),
        ],
        tier=Tier.COMMUNITY,
    )


def get_community_fail_repo() -> Repository:
    """Return main mock repo."""
    return Repository(
        name="mock-qiskit-terra-with-fail-dev-test",
        url="https://github.com/MockQiskit/mock-qiskit-wsdt-fail.terra",
        description="Mock description for repo. wsdt",
        licence="Apache 2.0",
        labels=["mock", "tests", "wsdt"],
        tests_results=[
            TestResult(
                passed=False,
                test_type=TestType.DEV_COMPATIBLE,
                package=Package.QISKIT,
                package_version="0.18.0",
            ),
            TestResult(
                passed=False,
                test_type=TestType.STANDARD,
                package=Package.QISKIT,
                package_version="0.18.0",
            ),
        ],
        tier=Tier.COMMUNITY,
    )


class TestManager(TestCase):
    """Test class for manager cli."""

    def setUp(self) -> None:
        self.path = "../resources"
        self.members_path = "{}/members.json".format(self.path)
        self._delete_members_json()
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

    def tearDown(self) -> None:
        self._delete_members_json()

    def _delete_members_json(self):
        """Deletes database file."""
        if os.path.exists(self.members_path):
            os.remove(self.members_path)
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def test_build_website(self):
        """Test the website builder function."""
        manager = Manager(root_path=f"{os.path.abspath(os.getcwd())}/../")
        self.assertIsInstance(manager.build_website(), str)

    def test_parser_issue(self):
        """Tests issue parsing function.
        Function: Manager
                -> parser_issue
        Args:
            issue_body
        """

        # Issue 1
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            Manager.parser_issue(self.issue_body)

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
            Manager.parser_issue(self.issue_body_2)

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

    @responses.activate
    def test_dispatch_repository(self):
        """Test github dispatch event.
        Function: Manager
                -> dispatch_check_workflow
        Args:
            Infos about repo
        Return: response.status
        """
        owner = "qiskit-community"
        repo = "ecosystem"
        responses.add(
            **{
                "method": responses.POST,
                "url": "https://api.github.com/repos/{owner}/{repo}/dispatches".format(
                    owner=owner, repo=repo
                ),
                "body": '{"status": "ok"}',
                "status": 200,
                "content_type": "application/json",
            }
        )
        manager = Manager(root_path=f"{os.path.abspath(os.getcwd())}/../")
        response = manager.dispatch_check_workflow(
            repo_url="https://github.com/Qiskit-demo/qiskit-demo",
            branch_name="awesome_branch",
            tier="COMMUNITY",
            token="<TOKEN>",
            owner=owner,
            repo=repo,
        )
        self.assertTrue(response)

    def test_update_badges(self):
        """Tests creating badges."""
        self._delete_members_json()

        commu_success = get_community_repo()
        commu_failed = get_community_fail_repo()
        dao = DAO(self.path)

        # insert entry
        dao.write(commu_success)
        dao.write(commu_failed)

        manager = Manager(root_path=os.path.join(self.current_dir, ".."))
        manager.resources_dir = "../resources"
        manager.dao = dao

        # create badges
        manager.update_badges()

        badges_folder_path = "{}/badges".format(manager.current_dir)
        self.assertTrue(
            os.path.isfile(f"{badges_folder_path}/{commu_success.name}.svg")
        )
        self.assertTrue(os.path.isfile(f"{badges_folder_path}/{commu_failed.name}.svg"))

        # check version status
        with open(
            f"{badges_folder_path}/{commu_success.name}.svg", "r"
        ) as svg_blueviolet:
            svg_success = svg_blueviolet.read()
        self.assertTrue('fill="blueviolet"' in svg_success)

        with open(f"{badges_folder_path}/{commu_failed.name}.svg", "r") as svg_grey:
            svg_failed = svg_grey.read()
        self.assertTrue('fill="blueviolet"' not in svg_failed)

        os.remove(f"{badges_folder_path}/{commu_success.name}.svg")
        os.remove(f"{badges_folder_path}/{commu_failed.name}.svg")

    @responses.activate
    def test_fetch_and_update_main_projects(self):
        """Tests manager function for fetching tests results."""
        owner = "Qiskit"
        repos_and_test_names = [
            ("qiskit-nature", "Nature%2520Unit%2520Tests"),
            ("qiskit-finance", "Finance%2520Unit%2520Tests"),
            ("qiskit-optimization", "Optimization%2520Unit%2520Tests"),
            ("qiskit-machine-learning", "Machine%2520Learning%2520Unit%2520Tests"),
            ("qiskit-experiments", "Tests"),
            ("qiskit-aer", "Tests%2520Linux"),
        ]

        for repo, test_name in repos_and_test_names:
            responses.add(
                **{
                    "method": responses.GET,
                    "url": "https://api.github.com/repos/{owner}/{repo}/actions/runs"
                    "?event=push&branch=main&name={test_name}&per_page=1".format(
                        owner=owner, repo=repo, test_name=test_name
                    ),
                    "body": '{"status": "ok"}',
                    "status": 200,
                    "content_type": "application/json",
                }
            )
        responses.add(
            **{
                "method": responses.GET,
                "url": "https://raw.githubusercontent.com/Qiskit/"
                "qiskit-terra/main/qiskit/VERSION.txt",
                "body": "0.19.0",
                "status": 200,
            }
        )
        responses.add(
            **{
                "method": responses.GET,
                "url": "https://api.github.com/repos/Qiskit/qiskit-terra/releases?per_page=1",
                "body": '[{"tag_name": "0.18.3"}]',
                "status": 200,
                "content_type": "application/json",
            }
        )

        manager = Manager(root_path=f"{os.path.abspath(os.getcwd())}/../")
        self.assertIsNone(manager.fetch_and_update_main_tests_results())
