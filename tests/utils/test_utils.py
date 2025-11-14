"""Tests for manager."""

import os
from unittest import TestCase

from ecosystem.member import Member
from ecosystem.submission_parser import parse_submission_issue
from ecosystem.dao import DAO


class TestUtils(TestCase):
    """Test class for manager functions."""

    def setUp(self) -> None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(f"{current_dir}/../resources/issue.md", "r") as issue_body_file:
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

        self.assertTrue(isinstance(parsed_result, Member))
        self.assertEqual(parsed_result.name, "Qiskit Banana Compiler")
        self.assertEqual(
            parsed_result.url, "https://github.com/somebody/banana-compiler"
        )
        self.assertEqual(
            parsed_result.description,
            "Compile bananas into Qiskit quantum circuits. "
            "Supports all modern devices, including Musa × paradisiaca.",
        )
        self.assertEqual(parsed_result.contact_info, "author@banana-compiler.org")
        self.assertEqual(parsed_result.affiliations, None)
        self.assertEqual(parsed_result.ibm_maintained, False)
        self.assertEqual(
            parsed_result.labels,
            ["error mitigation, quantum information, optimization"],
        )

    # def test_issue_template_matches_repository_model(self):
    #     """Make sure IDs in the issue template match attributes of the Submission model."""
    #     issue_template = yaml.load(
    #         Path(".github/ISSUE_TEMPLATE/01_submission.yml").read_text(),
    #         Loader=yaml.SafeLoader,
    #     )
    #     issue_ids = {
    #         field["id"]
    #         for field in issue_template["body"]
    #         if field["type"] != "markdown"
    #     } - {"terms"}
    #
    #     repo_fields = {attr.name for attr in dataclasses.fields(Member)}
    #     for issue_id in issue_ids:
    #         self.assertIn(
    #             issue_id,
    #             repo_fields,
    #             msg="\nA field exists in the issue template but not in the Submission class.",
    #         )

    def test_description_lengths(self):
        """Make sure IDs in the issue template match attributes of the Submission model."""
        dao = DAO("ecosystem/resources")
        for repo in dao.get_all():
            if repo.description and len(repo.description) > 135:
                raise AssertionError(
                    f'Description for "{repo.name}" is too long!\n'
                    f"Rephrase to under 135 characters (currently {len(repo.description)})"
                )
