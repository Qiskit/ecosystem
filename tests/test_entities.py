"""Tests for entities."""
import os
from unittest import TestCase
from ecosystem.entities import MainRepository
from ecosystem.controller import Controller


class TestController(TestCase):
    """Tests repository related functions."""

    def setUp(self) -> None:
        self.path = "./resources"
        self.members_path = "{}/members.json".format(self.path)
        self._delete_members_json()
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def tearDown(self) -> None:
        self._delete_members_json()

    def _delete_members_json(self):
        """Deletes database file."""
        if os.path.exists(self.members_path):
            os.remove(self.members_path)
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def test_repository_insert_and_delete(self):
        """Tests repository."""
        self._delete_members_json()

        main_repo = MainRepository(name="mock-qiskit-terra",
                                   url="https://github.com/MockQiskit/mock-qiskit.terra",
                                   description="Mock description for repo.",
                                   licence="Apache 2.0",
                                   labels=["mock", "tests"])
        controller = Controller(self.path)

        # insert entry
        controller.insert(main_repo)
        fetched_repo = controller.get_all_main()[0]
        self.assertEqual(main_repo, fetched_repo)
        self.assertEqual(main_repo.labels, fetched_repo.labels)

        # delete entry
        controller.delete(main_repo)
        self.assertEqual([], controller.get_all_main())
