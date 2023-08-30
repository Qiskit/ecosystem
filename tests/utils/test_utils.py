"""Tests for manager."""
import os
import io
from unittest import TestCase
from contextlib import redirect_stdout

from ecosystem.models.repository import Repository
from ecosystem.utils import parse_submission_issue, set_actions_output


class TestUtils(TestCase):
    """Test class for manager functions."""

    def setUp(self) -> None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(
            "{}/../resources/issue.md".format(current_dir), "r"
        ) as issue_body_file:
            self.issue_body = issue_body_file.read()

    def test_issue_parsing(self):
        """Tests issue parsing function:
        Function:
                -> parse_submission_issue
        Args:
            issue_body
        Return : Repository
        """
        parsed_result = parse_submission_issue(self.issue_body)

        self.assertTrue(isinstance(parsed_result, Repository))
        self.assertEqual(parsed_result.name, "awesome")
        self.assertEqual(parsed_result.url, "http://github.com/awesome/awesome")
        self.assertEqual(
            parsed_result.description,
            "An awesome repo for awesome project multiple paragraphs",
        )
        self.assertEqual(parsed_result.contact_info, "toto@gege.com")
        self.assertEqual(parsed_result.alternatives, "tititata")
        self.assertEqual(parsed_result.licence, "Apache License 2.0")
        self.assertEqual(parsed_result.affiliations, "_No response_")
        self.assertEqual(
            parsed_result.labels, ["tool", "tutorial", "paper implementation"]
        )

    def test_set_actions_output(self):
        """Test set actions output."""
        # Test ok -> ok
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            set_actions_output([("success", "this test is a success case!")])
        output_value = captured_output.getvalue()
        self.assertEqual(output_value, "success=this test is a success case!\n")

        # Test ok -> ko
        with self.assertRaises(AssertionError):
            set_actions_output(
                [
                    (
                        "fail",
                        """
                this test is a failed case,
                why ?
                because it's a multi-lines output
                and GITHUB_OUTPUT doesn't like that!
                """,
                    )
                ]
            )
