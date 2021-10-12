"""Tests for manager cli."""
import os
import io
import sys
from unittest import TestCase

from ecosystem.manager import Manager


class TestManager(TestCase):
    """Test class for manager cli."""

    def setUp(self) -> None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open("{}/resources/issue.md".format(current_dir), "r") as issue_body_file:
            self.issue_body = issue_body_file.read()

    def test_issue_parsing_cli(self):
        """ "Tests issue parsing function"""
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput
        Manager.parser_issue(self.issue_body)

        sys.stdout = sys.__stdout__
        output_value = capturedOutput.getvalue().split("\n")

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
