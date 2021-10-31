"""Tests for manager cli."""
import os
import io
import sys
from unittest import TestCase

import responses

from ecosystem.manager import Manager


class TestManager(TestCase):
    """Test class for manager cli."""

    def setUp(self) -> None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open("{}/resources/issue.md".format(current_dir), "r") as issue_body_file:
            self.issue_body = issue_body_file.read()

    def test_parser_issue(self):
        """ "Tests issue parsing function.
        Function: Manager
                -> parser_issue
        Args:
            issue_body
        """
        captured_output = io.StringIO()
        sys.stdout = captured_output
        Manager.parser_issue(self.issue_body)

        sys.stdout = sys.__stdout__
        output_value = captured_output.getvalue().split("\n")

        self.assertEqual(output_value[0], "::set-output name=SUBMISSION_NAME::awesome")
        self.assertEqual(
            output_value[1],
            "::set-output name=SUBMISSION_REPO::http://github.com/awesome/awesome",
        )
        self.assertEqual(
            output_value[2],
            "::set-output name=SUBMISSION_DESCRIPTION::An awesome repo for awesome project",
        )
        self.assertEqual(
            output_value[3], "::set-output name=SUBMISSION_LICENCE::Apache License 2.0"
        )
        self.assertEqual(
            output_value[4], "::set-output name=SUBMISSION_CONTACT::toto@gege.com"
        )
        self.assertEqual(
            output_value[5], "::set-output name=SUBMISSION_ALTERNATIVES::tititata"
        )
        self.assertEqual(
            output_value[6], "::set-output name=SUBMISSION_AFFILIATIONS::_No response_"
        )
        self.assertEqual(
            output_value[7], "::set-output name=SUBMISSION_LABELS::['tool', 'tutorial']"
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
            issue_id=str(42),
            branch_name="awesome_branch",
            tier="COMMUNITY",
            token="<TOKEN>",
            owner=owner,
            repo=repo,
        )
        self.assertTrue(response)
