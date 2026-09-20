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

"""Tests for ecosystem/check.py."""

import os
import tomllib
from datetime import date, timedelta
from unittest import TestCase
from unittest.mock import patch
import pytest

from ecosystem.check import CheckData
from ecosystem.error_handling import EcosystemError


class TestChecksTOML(TestCase):
    """Tests related to resources/checks.toml."""

    meta_categories = ["categories", "importance"]
    mandatory_keys = ["title", "description", "applies_to", "category", "importance"]
    optional_keys = [
        "checker",
        "affects",
        "related_to",
        "cure_period_in_days",
        "discussion",
    ]

    def setUp(self) -> None:

        class TestCollector:  # pylint: disable=missing-function-docstring
            """To collect the collected tests"""

            def __init__(self):
                self.collected = []

            def pytest_collection_modifyitems(self, items):
                for item in items:
                    self.collected.append(item.nodeid.split("/")[-1])

        testcollector = TestCollector()
        pytest.main(
            ["--collect-only", "-q", "ecosystem/validation"], plugins=[testcollector]
        )
        self.collected_checks = testcollector.collected

        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(f"{current_dir}/../resources/checks.toml", "rb") as checks_toml:
            self.checks_toml = tomllib.load(checks_toml)

    def test_valid_entries(self):
        """Tests entries in checks.toml have the right fields"""
        for id_, entry in self.checks_toml.items():
            if id_ in self.meta_categories:
                continue
            with self.subTest(id=id_):
                self.assertEqual(len(id_), 3, msg=f"{id_} is not a valid checkup ID")
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

    def assertHasNoDuplicates(self, iterable, msg=None):  # pylint: disable=invalid-name
        """Check for duplicated elements in iterable"""
        unique = set(iterable)
        if len(iterable) != len(set(iterable)):
            standard_msg = (
                f"There are repetitions: { {i: iterable.count(i) for i in unique
                                                       if iterable.count(i) > 1}
            }"
            )
            self.fail(self._formatMessage(msg, standard_msg))

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
                self.assertHasNoDuplicates([c["name"] for c in self.checks_toml[cat]])


class TestSourceBasedCheckData(TestCase):
    """Tests for check ups based on an issue (check.source) instead of on a checker"""

    issue_url = "https://github.com/rigetti/qiskit-rigetti/issues/53"
    details = "Rigetti provider is not compatible with a maintained version of Qiskit"

    def check_with_issue(self, state, state_reason=None, details=None):
        """A source-based CheckData, updated against an issue in the given state"""
        check = CheckData(
            "Q20",
            since="2026-07-09",
            source=self.issue_url,
            details=self.details if details is None else details,
        )
        with patch(
            "ecosystem.check.request_json",
            return_value={"state": state, "state_reason": state_reason},
        ):
            check.update_from_source()
        return check

    def test_source_is_kept(self):
        """check.source survives the round trip to a dict"""
        check = CheckData("Q20", since="2026-07-09", source=self.issue_url)
        self.assertEqual(check.source, self.issue_url)
        self.assertEqual(check.to_dict()["source"], self.issue_url)

    def test_no_source(self):
        """A check up without a source has source = None and update_from_source does nothing"""
        check = CheckData("Q20", since="2026-07-09", details=self.details)
        self.assertIsNone(check.source)
        check.update_from_source()
        self.assertEqual(check.details, self.details)

    def test_source_api_url(self):
        """The issue URL is translated into the GitHub API URL"""
        check = CheckData("Q20", source=self.issue_url)
        self.assertEqual(
            check.source_api_url,
            "https://api.github.com/repos/rigetti/qiskit-rigetti/issues/53",
        )

    def test_source_is_not_an_issue(self):
        """A source that is not a GitHub issue is an error"""
        check = CheckData("Q20", source="https://github.com/rigetti/qiskit-rigetti")
        with self.assertRaises(EcosystemError):
            check.source_api_url  # pylint: disable=pointless-statement

    def test_open_issue(self):
        """While the issue is open, the details are untouched"""
        check = self.check_with_issue("open")
        self.assertEqual(check.details, self.details)

    def test_closed_as_completed(self):
        """A closed as completed issue is annotated in the details"""
        check = self.check_with_issue("closed", "completed")
        self.assertEqual(
            check.details, f"{self.details} (the source issue is closed as completed)"
        )

    def test_closed_as_not_planned(self):
        """A closed as not planned issue is annotated in the details"""
        check = self.check_with_issue("closed", "not_planned")
        self.assertEqual(
            check.details, f"{self.details} (the source issue is closed as not planned)"
        )

    def test_closed_without_reason(self):
        """A closed issue without a state_reason is annotated too"""
        check = self.check_with_issue("closed")
        self.assertEqual(check.details, f"{self.details} (the source issue is closed)")

    def test_annotation_does_not_pile_up(self):
        """Running update_from_source twice does not repeat the annotation"""
        annotated = f"{self.details} (the source issue is closed as completed)"
        check = self.check_with_issue("closed", "completed", details=annotated)
        self.assertEqual(check.details, annotated)

    def test_reopened_issue_drops_the_annotation(self):
        """If the issue is open again, the annotation is removed"""
        annotated = f"{self.details} (the source issue is closed as not planned)"
        check = self.check_with_issue("open", "reopened", details=annotated)
        self.assertEqual(check.details, self.details)

    def test_no_checker(self):
        """A source-based check up has no checker, and asking for it is an AttributeError"""
        check = CheckData("020", since="2026-07-09", source=self.issue_url)
        self.assertIsNone(getattr(check, "checker", None))
        with self.assertRaises(AttributeError):
            check.checker  # pylint: disable=pointless-statement


class TestXfailedExpiration(TestCase):
    """Tests for the expiration date of an xfail explanation (check.xfailed_until)"""

    reason = "This project does not need to agree the CoC"

    def check(self, xfailed_until=None, xfailed=reason):
        """A CheckData with an explanation that expires on `xfailed_until`"""
        return CheckData("COC", xfailed=xfailed, xfailed_until=xfailed_until)

    def test_no_expiration(self):
        """An explanation without xfailed_until never expires"""
        check = self.check()
        self.assertIsNone(check.xfailed_until)
        self.assertFalse(check.xfailed_expired)
        self.assertTrue(check.xfail_applies)
        self.assertIsNone(check.days_until_xfailed_expires)

    def test_future_expiration(self):
        """An explanation that expires in the future still applies"""
        check = self.check(CheckData.today + timedelta(days=30))
        self.assertFalse(check.xfailed_expired)
        self.assertTrue(check.xfail_applies)
        self.assertEqual(check.days_until_xfailed_expires, 30)

    def test_expires_today(self):
        """The explanation is valid during the whole xfailed_until day"""
        check = self.check(CheckData.today)
        self.assertFalse(check.xfailed_expired)
        self.assertTrue(check.xfail_applies)
        self.assertEqual(check.days_until_xfailed_expires, 0)

    def test_past_expiration(self):
        """Once xfailed_until has passed, the explanation does not apply anymore"""
        check = self.check(CheckData.today - timedelta(days=1))
        self.assertTrue(check.xfailed_expired)
        self.assertFalse(check.xfail_applies)
        self.assertEqual(check.days_until_xfailed_expires, -1)

    def test_no_xfailed(self):
        """A check up without an explanation is never excused, expiration or not"""
        self.assertFalse(self.check(xfailed=None).xfail_applies)
        self.assertFalse(
            self.check(CheckData.today + timedelta(days=30), xfailed=None).xfail_applies
        )

    def test_expiration_is_parsed(self):
        """xfailed_until is normalized to a date and survives the round trip to a dict"""
        check = self.check("2027-01-31")
        self.assertEqual(check.xfailed_until, date(2027, 1, 31))
        self.assertEqual(check.to_dict()["xfailed_until"], date(2027, 1, 31))


class TestCurePeriod(TestCase):
    """Tests for the deadline a failing check up sets (check.cure_period_*)"""

    # [001] is CRITICAL, so its cure period is 0 days
    critical = "001"
    # [PQ2] is IMPORTANT, so its cure period is the 90 days of that importance level
    important = "PQ2"
    # [P10] states its own cure period, -1, instead of the default of its importance
    infinite = "P10"

    @staticmethod
    def check(id_, days_ago):
        """A CheckData for the check up `id_`, failing since `days_ago` days ago"""
        return CheckData(id_, since=CheckData.today - timedelta(days=days_ago))

    def test_zero_days_expires_the_next_day(self):
        """A cure period of 0 days lasts for the day the check up started failing"""
        self.assertFalse(self.check(self.critical, 0).cure_period_expired)
        self.assertTrue(self.check(self.critical, 1).cure_period_expired)

    def test_deadline_is_since_plus_the_cure_period(self):
        """The deadline does not move while the check up keeps failing"""
        check = self.check(self.important, 10)
        self.assertEqual(check.cure_period_in_days, 90)
        self.assertEqual(check.cure_period_deadline, check.since + timedelta(days=90))
        self.assertFalse(check.cure_period_is_infinite)
        self.assertFalse(check.cure_period_expired)

    def test_the_last_day_of_the_cure_period_is_not_expired(self):
        """There is still time to fix it on the deadline itself"""
        self.assertFalse(self.check(self.important, 90).cure_period_expired)
        self.assertTrue(self.check(self.important, 91).cure_period_expired)

    def test_negative_cure_period_is_infinite(self):
        """A negative cure_period_in_days means the cure period never runs out"""
        check = self.check(self.infinite, 10_000)
        self.assertEqual(check.cure_period_in_days, -1)
        self.assertTrue(check.cure_period_is_infinite)
        self.assertIsNone(check.cure_period_deadline)
        self.assertFalse(check.cure_period_expired)

    def test_no_since_has_no_deadline(self):
        """Without a `since` date there is nothing to count the cure period from"""
        check = CheckData(self.important)
        self.assertIsNone(check.cure_period_deadline)
        self.assertFalse(check.cure_period_expired)
