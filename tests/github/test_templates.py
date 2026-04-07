from ecosystem.labels import LabelsToml

"""Tests for GitHub Templates."""

import os
from unittest import TestCase
from ruamel.yaml import YAML

from ecosystem.member import Member
from ecosystem.submission_parser import parse_submission_issue
from ecosystem.dao import DAO


class Test01submission(TestCase):
    """Test class for .github/ISSUE_TEMPLATE/01_submission.yml"""

    def setUp(self) -> None:
        root_dir = f"{os.path.dirname(os.path.abspath(__file__))}/../../"
        self.labels_toml = LabelsToml(resources_dir=f"{root_dir}/ecosystem/resources")
        yaml = YAML()
        with open(
            f"{root_dir}/.github/ISSUE_TEMPLATE/01_submission.yml", "r"
        ) as issue_template_file:
            self.issue_template = yaml.load(issue_template_file)

    def test_categories(self):
        for section in self.issue_template["body"]:
            if "id" in section and section["id"] == "category":
                self.assertIn("attributes", section)
                self.assertIn("options", section["attributes"])
                self.assertEqual(
                    section["attributes"]["options"],
                    ["Select one..."] + self.labels_toml.category_names,
                )

    def test_labels(self):
        for section in self.issue_template["body"]:
            if "id" in section and section["id"] == "labels":
                self.assertIn("attributes", section)
                self.assertIn("options", section["attributes"])
                self.assertEqual(
                    section["attributes"]["options"], self.labels_toml.label_names
                )

    def test_interfaces(self):
        for section in self.issue_template["body"]:
            if "id" in section and section["id"] == "interfaces":
                self.assertIn("attributes", section)
                self.assertIn("options", section["attributes"])
                self.assertEqual(
                    section["attributes"]["options"], self.labels_toml.interface_names
                )
