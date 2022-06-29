"""Tests for entities."""
import os
from unittest import TestCase

from ecosystem.daos import JsonDAO
from ecosystem.models import TestResult, TestType, Tier
from ecosystem.models.repository import Repository


def get_main_repo() -> Repository:
    """Return main mock repo."""
    return Repository(
        name="mock-qiskit-terra-with-success-dev-test",
        url="https://github.com/MockQiskit/mock-qiskit-wsdt.terra",
        description="Mock description for repo. wsdt",
        licence="Apache 2.0",
        labels=["mock", "tests", "wsdt"],
        tests_results=[TestResult(True, "0.18.1", TestType.DEV_COMPATIBLE)],
        tier=Tier.MAIN,
    )


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
        """Deletes database file.
        Function: JsonDao
                -> delete
        """
        if os.path.exists(self.members_path):
            os.remove(self.members_path)
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def test_repository_insert_and_delete(self):
        """Tests repository."""
        self._delete_members_json()

        main_repo = get_main_repo()
        dao = JsonDAO(self.path)

        # insert entry
        dao.insert(main_repo)
        fetched_repo = dao.get_repos_by_tier(Tier.MAIN)[0]
        self.assertEqual(main_repo, fetched_repo)
        self.assertEqual(main_repo.labels, fetched_repo.labels)
        self.assertEqual(len(fetched_repo.tests_results), 1)

        # delete entry
        dao.delete(repo_url=main_repo.url, tier=main_repo.tier)
        self.assertEqual([], dao.get_repos_by_tier(Tier.MAIN))

    def test_move_from_tier_to_tier(self):
        """Tests moving repo from tier to tier.
        Function: JsonDao
                -> move_repo_to_other_tier
        """
        self._delete_members_json()

        main_repo = get_main_repo()
        dao = JsonDAO(self.path)

        # insert entry
        dao.insert(main_repo)
        fetched_repo = dao.get_repos_by_tier(Tier.MAIN)[0]
        self.assertEqual(main_repo, fetched_repo)
        self.assertEqual(main_repo.labels, fetched_repo.labels)
        self.assertEqual(len(fetched_repo.tests_results), 1)

        # move from tier to tier
        moved_repo = dao.move_repo_to_other_tier(
            repo_url=main_repo.url,
            source_tier=main_repo.tier,
            destination_tier=Tier.COMMUNITY,
        )
        repos = dao.get_repos_by_tier(Tier.MAIN)
        self.assertEqual(len(repos), 0)

        candidate_repos = dao.get_repos_by_tier(Tier.COMMUNITY)
        self.assertEqual(len(candidate_repos), 1)
        self.assertEqual(candidate_repos[0], moved_repo)

    def test_add_test_result(self):
        """Tests adding result to repo.
        JsonDao
                -> add_repo_test_result
        """
        self._delete_members_json()
        dao = JsonDAO(self.path)

        main_repo = get_main_repo()
        dao.insert(main_repo)
        res = dao.add_repo_test_result(
            main_repo.url,
            main_repo.tier,
            TestResult(False, "0.18.1", TestType.DEV_COMPATIBLE),
        )
        self.assertEqual(res, [1])
        recovered_repo = dao.get_by_url(main_repo.url, tier=main_repo.tier)
        self.assertEqual(
            recovered_repo.tests_results,
            [TestResult(False, "0.18.1", TestType.DEV_COMPATIBLE)],
        )
        self.assertEqual(
            recovered_repo.historical_test_results,
            [TestResult(False, "0.18.1", TestType.DEV_COMPATIBLE)],
        )

        res = dao.add_repo_test_result(
            main_repo.url,
            main_repo.tier,
            TestResult(True, "0.18.2", TestType.DEV_COMPATIBLE),
        )
        self.assertEqual(res, [1])
        res = dao.add_repo_test_result(
            main_repo.url,
            main_repo.tier,
            TestResult(True, "0.18.2", TestType.STANDARD),
        )
        self.assertEqual(res, [1])
        recovered_repo = dao.get_by_url(main_repo.url, tier=main_repo.tier)
        self.assertEqual(
            recovered_repo.tests_results,
            [
                TestResult(True, "0.18.2", TestType.DEV_COMPATIBLE),
                TestResult(True, "0.18.2", TestType.STANDARD),
            ],
        )
        self.assertEqual(
            recovered_repo.historical_test_results,
            [
                TestResult(False, "0.18.1", TestType.DEV_COMPATIBLE),
                TestResult(True, "0.18.2", TestType.DEV_COMPATIBLE),
                TestResult(True, "0.18.2", TestType.STANDARD),
            ],
        )

    def test_add_test_result_order(self):
        """Test order of test results."""
        self._delete_members_json()
        dao = JsonDAO(self.path)

        main_repo = get_main_repo()
        dao.insert(main_repo)
        dao.add_repo_test_result(
            main_repo.url,
            main_repo.tier,
            TestResult(False, "0.18.1", TestType.STABLE_COMPATIBLE),
        )
        dao.add_repo_test_result(
            main_repo.url,
            main_repo.tier,
            TestResult(False, "0.18.1", TestType.STANDARD),
        )
        dao.add_repo_test_result(
            main_repo.url,
            main_repo.tier,
            TestResult(False, "0.18.1", TestType.DEV_COMPATIBLE),
        )

        recovered_repo = dao.get_by_url(main_repo.url, tier=main_repo.tier)
        test_results = recovered_repo.tests_results
        self.assertEqual(test_results[0].test_type, TestType.DEV_COMPATIBLE)
        self.assertEqual(test_results[1].test_type, TestType.STABLE_COMPATIBLE)
        self.assertEqual(test_results[2].test_type, TestType.STANDARD)
