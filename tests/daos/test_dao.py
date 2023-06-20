"""Tests for entities."""
import os
import json
from unittest import TestCase

from ecosystem.daos import JsonDAO
from ecosystem.models import TestResult, TestType, Tier
from ecosystem.models.repository import Repository
from ecosystem.models.test_results import Package


def get_main_repo() -> Repository:
    """Return main mock repo."""
    return Repository(
        name="mock-qiskit-terra-with-success-dev-test",
        url="https://github.com/MockQiskit/mock-qiskit-wsdt.terra",
        description="Mock description for repo. wsdt",
        licence="Apache 2.0",
        labels=["mock", "tests", "wsdt"],
        tests_results=[],
        tier=Tier.MAIN,
    )


class TestJsonDao(TestCase):
    """Tests repository related functions."""

    def setUp(self) -> None:
        self.path = "../resources"
        self.members_path = "{}/members.json".format(self.path)
        self.labels_path = "{}/labels.json".format(self.path)
        self._delete_members_json()
        self._create_dummy_labels_json()
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

    def _delete_labels_json(self):
        """Deletes labels file.
        Function: JsonDao
                -> delete
        """
        if os.path.exists(self.labels_path):
            os.remove(self.labels_path)
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def test_start_update(self):
        """Test update start for repo."""
        self._delete_members_json()
        main_repo = get_main_repo()
        dao = JsonDAO(self.path)
        dao.insert(main_repo)

        repo_from_db = dao.get_by_url(main_repo.url, main_repo.tier)
        self.assertIsNone(repo_from_db.stars)

        dao.update_stars(main_repo.url, main_repo.tier, 42)
        repo_from_db = dao.get_by_url(main_repo.url, main_repo.tier)
        self.assertEqual(repo_from_db.stars, 42)

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
        self.assertEqual(len(fetched_repo.tests_results), 0)

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
        self.assertEqual(len(fetched_repo.tests_results), 0)

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

    def test_latest_results(self):
        """Tests append of latest passed test results."""
        self._delete_members_json()
        dao = JsonDAO(self.path)
        main_repo = get_main_repo()
        dao.insert(main_repo)

        dao.add_repo_test_result(
            repo_url=main_repo.url,
            tier=main_repo.tier,
            test_result=TestResult(
                passed=True,
                test_type=TestType.STANDARD,
                package=Package.TERRA,
                package_version="0.18.1",
            ),
        )
        recovered_repo = dao.get_by_url(main_repo.url, tier=main_repo.tier)
        self.assertEqual(len(recovered_repo.tests_results), 1)

        dao.add_repo_test_result(
            repo_url=main_repo.url,
            tier=main_repo.tier,
            test_result=TestResult(
                passed=True,
                test_type=TestType.DEV_COMPATIBLE,
                package=Package.TERRA,
                package_version="0.18.1",
            ),
        )
        recovered_repo = dao.get_by_url(main_repo.url, tier=main_repo.tier)
        self.assertEqual(len(recovered_repo.tests_results), 2)

        dao.add_repo_test_result(
            repo_url=main_repo.url,
            tier=main_repo.tier,
            test_result=TestResult(
                passed=False,
                test_type=TestType.STABLE_COMPATIBLE,
                package=Package.TERRA,
                package_version="0.18.1",
            ),
        )
        recovered_repo = dao.get_by_url(main_repo.url, tier=main_repo.tier)
        self.assertEqual(len(recovered_repo.tests_results), 3)

        # here latest passed should be added
        dao.add_repo_test_result(
            repo_url=main_repo.url,
            tier=main_repo.tier,
            test_result=TestResult(
                passed=True,
                test_type=TestType.STABLE_COMPATIBLE,
                package=Package.TERRA,
                package_version="0.18.1",
            ),
        )
        recovered_repo = dao.get_by_url(main_repo.url, tier=main_repo.tier)
        self.assertEqual(len(recovered_repo.tests_results), 4)
        self.assertIn(
            TestResult(
                passed=True,
                test_type=TestType.LAST_WORKING_VERSION,
                package=Package.TERRA,
                package_version="0.18.1",
            ),
            recovered_repo.tests_results,
        )

        # here we check that last passed is updated
        dao.add_repo_test_result(
            repo_url=main_repo.url,
            tier=main_repo.tier,
            test_result=TestResult(
                passed=True,
                test_type=TestType.STABLE_COMPATIBLE,
                package=Package.TERRA,
                package_version="0.20.0",
            ),
        )
        recovered_repo = dao.get_by_url(main_repo.url, tier=main_repo.tier)
        self.assertEqual(len(recovered_repo.tests_results), 4)
        self.assertIn(
            TestResult(
                passed=True,
                test_type=TestType.LAST_WORKING_VERSION,
                package=Package.TERRA,
                package_version="0.20.0",
            ),
            recovered_repo.tests_results,
        )

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
            TestResult(
                passed=False,
                test_type=TestType.DEV_COMPATIBLE,
                package=Package.TERRA,
                package_version="0.18.1",
            ),
        )
        self.assertEqual(res, [1])
        self.assertLabelsFile(
            [
                {"description": "description for label 1", "name": "label 1"},
                {"description": "description for label 2", "name": "label 2"},
                {"description": "description for label 4", "name": "label 4"},
                {"description": "", "name": "mock"},
                {"description": "", "name": "tests"},
                {"description": "", "name": "wsdt"},
            ]
        )

        recovered_repo = dao.get_by_url(main_repo.url, tier=main_repo.tier)
        self.assertEqual(
            recovered_repo.tests_results,
            [
                TestResult(
                    passed=False,
                    test_type=TestType.DEV_COMPATIBLE,
                    package=Package.TERRA,
                    package_version="0.18.1",
                )
            ],
        )
        self.assertEqual(
            recovered_repo.historical_test_results,
            [
                TestResult(
                    passed=False,
                    test_type=TestType.DEV_COMPATIBLE,
                    package=Package.TERRA,
                    package_version="0.18.1",
                )
            ],
        )

        res = dao.add_repo_test_result(
            main_repo.url,
            main_repo.tier,
            TestResult(
                passed=True,
                test_type=TestType.DEV_COMPATIBLE,
                package=Package.TERRA,
                package_version="0.18.2",
            ),
        )
        self.assertEqual(res, [1])
        res = dao.add_repo_test_result(
            main_repo.url,
            main_repo.tier,
            TestResult(
                passed=False,
                test_type=TestType.STANDARD,
                package=Package.TERRA,
                package_version="0.18.2",
            ),
        )
        self.assertEqual(res, [1])
        recovered_repo = dao.get_by_url(main_repo.url, tier=main_repo.tier)
        self.assertEqual(
            recovered_repo.tests_results,
            [
                TestResult(
                    passed=True,
                    test_type=TestType.DEV_COMPATIBLE,
                    package=Package.TERRA,
                    package_version="0.18.2",
                ),
                TestResult(
                    passed=False,
                    test_type=TestType.STANDARD,
                    package=Package.TERRA,
                    package_version="0.18.2",
                ),
            ],
        )
        self.assertEqual(
            recovered_repo.historical_test_results,
            [
                TestResult(
                    passed=False,
                    test_type=TestType.DEV_COMPATIBLE,
                    package=Package.TERRA,
                    package_version="0.18.1",
                ),
                TestResult(
                    passed=True,
                    test_type=TestType.DEV_COMPATIBLE,
                    package=Package.TERRA,
                    package_version="0.18.2",
                ),
                TestResult(
                    passed=False,
                    test_type=TestType.STANDARD,
                    package=Package.TERRA,
                    package_version="0.18.2",
                ),
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
            TestResult(
                passed=False,
                test_type=TestType.STABLE_COMPATIBLE,
                package=Package.TERRA,
                package_version="0.18.1",
            ),
        )
        dao.add_repo_test_result(
            main_repo.url,
            main_repo.tier,
            TestResult(
                passed=False,
                test_type=TestType.STANDARD,
                package=Package.TERRA,
                package_version="0.18.1",
            ),
        )
        dao.add_repo_test_result(
            main_repo.url,
            main_repo.tier,
            TestResult(
                passed=False,
                test_type=TestType.DEV_COMPATIBLE,
                package=Package.TERRA,
                package_version="0.18.1",
            ),
        )

        recovered_repo = dao.get_by_url(main_repo.url, tier=main_repo.tier)
        test_results = recovered_repo.tests_results
        self.assertEqual(test_results[0].test_type, TestType.DEV_COMPATIBLE)
        self.assertEqual(test_results[1].test_type, TestType.STABLE_COMPATIBLE)
        self.assertEqual(test_results[2].test_type, TestType.STANDARD)

    def assertLabelsFile(self, result):  # pylint: disable=invalid-name
        """Asserts the content of labels.json matches the result dict"""
        with open(self.labels_path, "r") as labels_file:
            content = json.load(labels_file)
        self.assertEqual(content, result)

    def _create_dummy_labels_json(self):
        dummy_data = [
            {"name": "label 1", "description": "description for label 1"},
            {"name": "label 2", "description": "description for label 2"},
            {"name": "label 4", "description": "description for label 4"},
        ]
        with open(self.labels_path, "w") as labels_file:
            json.dump(dummy_data, labels_file)
