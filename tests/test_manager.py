"""Tests for manager."""
from unittest import TestCase
from ecosystem.entities import Repository
from ecosystem.manager import parse_submission_issue


class TestManager(TestCase):
    """Test class for manager functions."""

    def setUp(self) -> None:
        with open("tests/ressources/issue.md", "r") as issue_body_file:
            self.issue_body = issue_body_file.read()

    def test_issue_parsing(self):
        """"Tests issue parsing function"""
        parsed_result = parse_submission_issue(self.issue_body)

        self.assertTrue(isinstance(parsed_result, Repository))
        self.assertEqual(parsed_result.name, "awesome")
        self.assertEqual(parsed_result.url, "http://github.com/awesome/awesome")
        self.assertEqual(parsed_result.description, "An awesome repo for awesome project")
        self.assertEqual(parsed_result.contact_info, "toto@gege.com")
        self.assertEqual(parsed_result.alternatives, "tititata")
        self.assertEqual(parsed_result.licence, "Apache License 2.0")
        self.assertEqual(parsed_result.affiliations, "_No response_")
        self.assertEqual(parsed_result.labels, ["tool", "tutorial"])
