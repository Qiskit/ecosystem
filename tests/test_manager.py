"""Tests for manager."""
from unittest import TestCase
from ecosystem.entities import Repository
from ecosystem.manager import parse_submission_issue


class TestManager(TestCase):
    """Test class for manager functions."""

    def test_issue_parsing(self):
        """"Tests issue parsing function"""
        issue_body = """### Github repo

http://github.com/awesome/awesome

### Description

An awesome repo for awesome project

### Email

toto@gege.com

### Alternatives

tititata

### License

Apache License 2.0

### Affiliations

_No response_

### Tags

tool, tutorial"""
        parsed_result = parse_submission_issue(issue_body)

        self.assertTrue(isinstance(Repository, parse_submission_issue))
        self.assertEqual(parsed_result.name, "awesome")
        self.assertEqual(parsed_result.url, "http://github.com/awesome/awesome")
        self.assertEqual(parsed_result.description, "An awesome repo for awesome project")
        self.assertEqual(parsed_result.contact_info, "toto@gege.com")
        self.assertEqual(parsed_result.alternatives, "tititata")
        self.assertEqual(parsed_result.license, "Apache License 2.0")
        self.assertEqual(parsed_result.affiliations, "_No response_")
        self.assertEqual(parsed_result.labels, ["tool", "tutorial"])
