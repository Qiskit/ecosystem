"""Tests for GitHub Templates."""

import os
from unittest import TestCase
from ruamel.yaml import YAML

from ecosystem.classifications import ClassificationsToml


class Test01submission(TestCase):
    """Test class for .github/ISSUE_TEMPLATE/01_submission.yml"""

    def setUp(self) -> None:
        root_dir = f"{os.path.dirname(os.path.abspath(__file__))}/../../"
        self.classifications_toml = ClassificationsToml(
            resources_dir=f"{root_dir}/resources"
        )

        def show_in_submission_template(x):
            return (
                x["show_in_submission_template"]
                if "show_in_submission_template" in x
                else True
            )

        self.classifications_toml.set_filter(show_in_submission_template)
        yaml = YAML()
        with open(
            f"{root_dir}/.github/ISSUE_TEMPLATE/01_submission.yml", "r"
        ) as issue_template_file:
            self.issue_template = yaml.load(issue_template_file)

    def test_categories(self):
        """categories_names in the template should exist in classifications.toml"""
        for section in self.issue_template["body"]:
            if "id" in section and section["id"] == "category":
                self.assertIn("attributes", section)
                self.assertIn("options", section["attributes"])
                self.assertEqual(
                    list(section["attributes"]["options"]),
                    ["Select one..."] + self.classifications_toml.category_names,
                )

    def test_labels(self):
        """labels in the issue template should exist in classsifications.toml"""
        for section in self.issue_template["body"]:
            if "id" in section and section["id"] == "labels":
                self.assertIn("attributes", section)
                self.assertIn("options", section["attributes"])
                self.assertEqual(
                    list(section["attributes"]["options"]),
                    self.classifications_toml.labels_names,
                )

    def test_interfaces(self):
        """interfaces in the template should exist in classifications.toml"""
        for section in self.issue_template["body"]:
            if "id" in section and section["id"] == "interfaces":
                self.assertIn("attributes", section)
                self.assertIn("options", section["attributes"])
                self.assertEqual(
                    section["attributes"]["options"],
                    self.classifications_toml.interfaces_names,
                )

    def test_maturity(self):
        """maturity classification in the template should exist in classifications.toml"""
        for section in self.issue_template["body"]:
            if "id" in section and section["id"] == "maturity":
                self.assertIn("attributes", section)
                self.assertIn("options", section["attributes"])
                self.assertEqual(
                    list(section["attributes"]["options"]),
                    self.classifications_toml.maturity_names,
                )

    def test_pattern_step(self):
        """Qiskit pattern step in the template should exist in classifications.toml"""
        for section in self.issue_template["body"]:
            if "id" in section and section["id"] == "pattern_step":
                self.assertIn("attributes", section)
                self.assertIn("options", section["attributes"])
                self.assertEqual(
                    section["attributes"]["options"],
                    self.classifications_toml.interface_names,
                )
