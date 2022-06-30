"""Tests for memebers json file."""
import json
import os
from unittest import TestCase

from ecosystem.daos import JsonDAO
from ecosystem.models import Tier
from ecosystem.models.repository import Repository


class TestMembersJson(TestCase):
    """Tests for members file."""

    def setUp(self) -> None:
        current_directory = os.path.dirname(os.path.abspath(__file__))
        self.path = "{}/../ecosystem/resources".format(current_directory)
        self.members_path = "{}/members.json".format(self.path)
        self.dao = JsonDAO(self.path)

    def test_members_json(self):
        """Tests members json file for correctness."""
        self.assertTrue(os.path.exists(self.members_path))
        with open(self.members_path, "r") as members_file:
            members_data = json.load(members_file)
            self.assertIsInstance(members_data, dict)

    def test_deserialize_to_repositories(self):
        """Tests members json deserialization."""
        community_repos = self.dao.get_repos_by_tier(Tier.COMMUNITY)
        self.assertTrue(len(community_repos) > 0)
        for repo in community_repos:
            self.assertIsInstance(repo, Repository)
            self.assertIn(repo.skip_tests, [True, False, None])
            for result in repo.tests_results:
                self.assertIsNotNone(result.package)
                self.assertIsNotNone(result.package_version)
                self.assertEqual(result.package_version, result.terra_version)
