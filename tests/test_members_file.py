"""Tests for memebers json file."""
import json
import os
from unittest import TestCase


class TestMembersJson(TestCase):
    """Tests for members file."""

    def setUp(self) -> None:
        current_directory = os.path.dirname(os.path.abspath(__file__))
        self.path = "{}/../ecosystem/resources".format(current_directory)
        self.members_path = "{}/members.json".format(self.path)

    def test_members_json(self):
        """Tests members json file for correctness."""
        self.assertTrue(os.path.exists(self.members_path))
        with open(self.members_path, "r") as members_file:
            members_data = json.load(members_file)
            self.assertIsInstance(members_data, dict)
