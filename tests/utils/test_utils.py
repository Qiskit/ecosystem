"""Tests for manager."""

import os
import dataclasses
from unittest import TestCase
from pathlib import Path

import yaml

from ecosystem.models.submission import Submission
from ecosystem.utils import parse_submission_issue
from ecosystem.daos import DAO


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
        Return : Submission
        """
        parsed_result = parse_submission_issue(self.issue_body)

        self.assertTrue(isinstance(parsed_result, Submission))
        self.assertEqual(parsed_result.name, "My awesome project")
        self.assertEqual(parsed_result.url, "http://github.com/awesome/awesome")
        self.assertEqual(
            parsed_result.description,
            "An awesome repo for awesome project multiple paragraphs",
        )
        self.assertEqual(parsed_result.contact_info, "toto@gege.com")
        self.assertEqual(parsed_result.alternatives, "tititata")
        self.assertEqual(parsed_result.licence, "Apache License 2.0")
        self.assertEqual(parsed_result.affiliations, None)
        self.assertEqual(parsed_result.ibm_maintained, True)
        self.assertEqual(
            parsed_result.labels, ["tool", "tutorial", "paper implementation"]
        )

    def test_issue_template_matches_repository_model(self):
        """Make sure IDs in the issue template match attributes of the Submission model."""
        issue_template = yaml.load(
            Path(".github/ISSUE_TEMPLATE/submission.yml").read_text(),
            Loader=yaml.SafeLoader,
        )
        issue_ids = {
            field["id"]
            for field in issue_template["body"]
            if field["type"] != "markdown"
        }

        repo_fields = {attr.name for attr in dataclasses.fields(Submission)}
        for issue_id in issue_ids:
            self.assertIn(
                issue_id,
                repo_fields,
                msg="\nA field exists in the issue template but not in the Submission class.",
            )

    def test_decription_lengths(self):
        """Make sure IDs in the issue template match attributes of the Submission model."""
        # pylint: disable=no-self-use
        dao = DAO("ecosystem/resources")
        for repo in dao.get_all():
            if len(repo.description) > 135:
                raise AssertionError(
                    f'Description for "{repo.name}" is too long!\n'
                    f"Rephrase to under 135 characters (currently {len(repo.description)})"
                )
