"""Tests for entities."""
import os
from unittest import TestCase
from ecosystem.models import TestResult, TestType
from ecosystem.daos import JsonDAO
from ecosystem.models.repository import Repository


def get_main_repo() -> Repository:
    """Return main mock repo."""
    return Repository(name="mock-qiskit-terra-with-success-dev-test",
                      url="https://github.com/MockQiskit/mock-qiskit-wsdt.terra",
                      description="Mock description for repo. wsdt",
                      licence="Apache 2.0",
                      labels=["mock", "tests", "wsdt"],
                      tests_results=[
                          TestResult(True, "0.18.1", TestType.DEV_COMPATIBLE)])


class TestJsonDao(TestCase):
    """Tests repository related functions."""

    def setUp(self) -> None:
        self.path = "../resources"
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

        main_repo = get_main_repo()
        controller = JsonDAO(self.path)

        # insert entry
        controller.insert(main_repo)
        fetched_repo = controller.get_all_main()[0]
        self.assertEqual(main_repo, fetched_repo)
        self.assertEqual(main_repo.labels, fetched_repo.labels)
        self.assertEqual(len(fetched_repo.tests_results), 1)

        # delete entry
        controller.delete(main_repo)
        self.assertEqual([], controller.get_all_main())

    def test_add_test_result(self):
        """Tests adding result to repo."""
        self._delete_members_json()
        controller = JsonDAO(self.path)

        main_repo = get_main_repo()
        controller.insert(main_repo)
        res = controller.add_repo_test_result(main_repo.url,
                                              main_repo.tier,
                                              TestResult(False, "0.18.1",
                                                         TestType.DEV_COMPATIBLE))
        self.assertEqual(res, [1])
        recovered_repo = controller.get_by_url(main_repo.url, tier=main_repo.tier)
        self.assertEqual(recovered_repo.tests_results, [TestResult(False, "0.18.1",
                                                                   TestType.DEV_COMPATIBLE)])

        res = controller.add_repo_test_result(main_repo.url,
                                              main_repo.tier,
                                              TestResult(True, "0.18.2",
                                                         TestType.DEV_COMPATIBLE))
        self.assertEqual(res, [1])
        recovered_repo = controller.get_by_url(main_repo.url, tier=main_repo.tier)
        self.assertEqual(recovered_repo.tests_results, [TestResult(False, "0.18.1",
                                                                   TestType.DEV_COMPATIBLE),
                                                        TestResult(True, "0.18.2",
                                                                   TestType.DEV_COMPATIBLE)])
