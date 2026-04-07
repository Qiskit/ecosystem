"""Tests for ecosystem/check.py."""

import os
import pytest
import tomllib
from unittest import TestCase


class TestChecksTOML(TestCase):
    """Tests related to ecosystem/resources/checks.toml."""

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
