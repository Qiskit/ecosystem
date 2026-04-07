"""Tests for ecosystem/check.py."""

import os
import pytest
import tomllib
from unittest import TestCase


class TestChecksTOML(TestCase):
    """Tests related to ecosystem/resources/checks.toml."""

    meta_categories = ["categories", "importance"]
    mandatory_keys = ["title", "description", "applies_to", "category", "importance"]
    optional_keys = ["checker", "affects", "related_to"]

    def setUp(self) -> None:

        class TestCollector:
            def __init__(self):
                self.collected = []

            def pytest_collection_modifyitems(self, items):
                for item in items:
                    self.collected.append(item.nodeid.split("/")[-1])

        testcollector = TestCollector()
        pytest.main(["--collect-only", "ecosystem/validation"], plugins=[testcollector])
        self.collected_checks = testcollector.collected

        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(
            f"{current_dir}/../ecosystem/resources/checks.toml", "rb"
        ) as checks_toml:
            self.checks_toml = tomllib.load(checks_toml)

    def test_valid_entries(self):
        """Tests entries in checks.toml have the right fields"""
        for id, entry in self.checks_toml.items():
            if id in self.meta_categories:
                continue
            with self.subTest(id=id):
                self.assertEqual(len(id), 3, msg=f"{id} is not a valid checkup ID")
                for mandatory_key in self.mandatory_keys:
                    self.assertIn(
                        mandatory_key, entry, f"mandatory key {mandatory_key} missed"
                    )
                for key, value in entry.items():
                    self.assertIn(key, self.mandatory_keys + self.optional_keys)
                    if key in self.collected_checks:
                        self.assertIn(value, self.checks_toml[key])

    def test_checkups_exist_in_toml(self):
        """Tests if all the collect checkups exist in checks.toml"""
        checkers_in_toml = [
            check["checker"]
            for check in self.checks_toml.values()
            if "checker" in check
        ]
        for collected_check in self.collected_checks:
            with self.subTest(collected_check):
                self.assertIn(collected_check, checkers_in_toml)

    def test_toml_checkers_exist_in_pytest_collection(self):
        """Tests if all the checkers in checks.toml exist in the pytest collection"""
        checkers_in_toml = [
            check["checker"]
            for check in self.checks_toml.values()
            if "checker" in check
        ]
        for checker_in_toml in checkers_in_toml:
            with self.subTest(checker_in_toml):
                self.assertIn(checker_in_toml, self.collected_checks)

    def assertHasNoDuplicates(self, iterable, msg=None):
        """Check for duplicated elements in iterable"""
        unique = set(iterable)
        if len(iterable) != len(set(iterable)):
            standardMsg = "There are repetitions: %" % (
                {i: iterable.count(i) for i in unique if iterable.count(i) > 1},
            )
            self.fail(self._formatMessage(msg, standardMsg))

    def test_checkers_entries(self):
        """Tests if titles in checks.toml are unique. If not, probably a bad copy-paste"""
        titles_in_toml = [
            check["title"] for check in self.checks_toml.values() if "checker" in check
        ]
        self.assertHasNoDuplicates(titles_in_toml)

    def test_uniq_items_in_metacategories(self):
        """Tests if names in meta categories are unique."""
        for cat in self.meta_categories:
            with self.subTest(cat):
                self.assertHasNoDuplicates([c["name"] for c in cat])
