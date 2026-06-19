# This code is part of Qiskit.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Tests for manager."""

import os
from unittest import TestCase
from pathlib import Path
import yaml


from ecosystem.member import Member
from ecosystem.submission_parser import parse_submission_issue
from ecosystem.issue_body import EcosystemIssueBody as IssueBody


class TestUtils(TestCase):
    """Test class for manager functions."""

    def setUp(self) -> None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.issue_body = Path(f"{current_dir}/../resources/issue.md").read_text()

    def test_issue_body_to_dict(self):
        """Test ecosystem.submission_parser.issue_body_to_dict
        Takes text like:
           ### header 1

           body 1
        and converts it into a dict {'header 1': 'body 1'}
        """
        issue_template = yaml.load(
            Path(".github/ISSUE_TEMPLATE/01_submission.yml").read_text(),
            Loader=yaml.SafeLoader,
        )

        issue_body = IssueBody(self.issue_body, issue_template)
        self.assertEqual(issue_body.sections['Project name'], 'Qiskit Banana Compiler')

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
            ["error mitigation", "quantum information", "optimization"],
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
