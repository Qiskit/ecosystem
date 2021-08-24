"""Tests for entities."""
import os
from unittest import TestCase
from ecosystem.entities import MainRepository, TestType
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

    def test_add_and_remove_repo_test_passed(self):
        """Tests addition of passed test to repo."""
        self._delete_members_json()
        main_repo = MainRepository(name="mock-qiskit-terra",
                                   url="https://github.com/MockQiskit/mock-qiskit.terra",
                                   description="Mock description for repo.",
                                   licence="Apache 2.0",
                                   labels=["mock", "tests"])
        controller = Controller(self.path)
        controller.insert(main_repo)

        controller.add_repo_test_passed(repo_url=main_repo.url,
                                        test_passed=TestType.STANDARD,
                                        tier=main_repo.tier)
        fetched_repo = controller.get_by_url(main_repo.url, tier=main_repo.tier)
        self.assertEqual(fetched_repo.tests_passed, [TestType.STANDARD])

        controller.remove_repo_test_passed(repo_url=main_repo.url,
                                           test_remove=TestType.STANDARD,
                                           tier=main_repo.tier)
        fetched_repo = controller.get_by_url(main_repo.url, tier=main_repo.tier)
        self.assertEqual(fetched_repo.tests_passed, [])

    def test_update_repo_tests_passed(self):
        """Tests repository tests passed field."""
        self._delete_members_json()

        url = "https://github.com/MockQiskit/mock-qiskit.terra"
        main_repo = MainRepository(name="mock-qiskit-terra",
                                   url=url,
                                   description="Mock description for repo.",
                                   licence="Apache 2.0",
                                   labels=["mock", "tests"])
        controller = Controller(self.path)
        controller.insert(main_repo)

        controller.update_repo_tests_passed(main_repo, [TestType.STANDARD])
        fetched_repo = controller.get_by_url(url, main_repo.tier)
        self.assertEqual(len(fetched_repo.tests_passed), 1)
        self.assertEqual(fetched_repo.tests_passed, [TestType.STANDARD])

        controller.update_repo_tests_passed(main_repo, [TestType.STANDARD,
                                                        TestType.DEV_COMPATIBLE])
        fetched_repo = controller.get_by_url(url, main_repo.tier)
        self.assertEqual(len(fetched_repo.tests_passed), 2)
        self.assertEqual(fetched_repo.tests_passed, [TestType.STANDARD,
                                                     TestType.DEV_COMPATIBLE])

        controller.update_repo_tests_passed(main_repo, [])
        fetched_repo = controller.get_by_url(url, main_repo.tier)
        self.assertEqual(len(fetched_repo.tests_passed), 0)
        self.assertEqual(fetched_repo.tests_passed, [])
