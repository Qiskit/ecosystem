"""Tests for entities."""
import os
import json
from unittest import TestCase

from ecosystem.daos import DAO
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


class TestDao(TestCase):
    """Tests repository related functions."""

    def setUp(self) -> None:
        self.path = "../resources"
        self.labels_path = "{}/labels.json".format(self.path)
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        self._create_dummy_labels_json()

    def _delete_labels_json(self):
        """Deletes labels file.
        Function: Dao
                -> delete
        """
        if os.path.exists(self.labels_path):
            os.remove(self.labels_path)
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def test_start_update(self):
        """Test update start for repo."""
        main_repo = get_main_repo()
        dao = DAO(self.path)
        dao.write(main_repo)

        repo_from_db = dao.get_by_url(main_repo.url)
        self.assertIsNone(repo_from_db.stars)

        dao.update(main_repo.url, stars=42)
        repo_from_db = dao.get_by_url(main_repo.url)
        self.assertEqual(repo_from_db.stars, 42)

    def test_repository_insert_and_delete(self):
        """Tests repository."""
        main_repo = get_main_repo()
        dao = DAO(self.path)

        # insert entry
        dao.write(main_repo)
        fetched_repo = dao.get_repos_by_tier(Tier.MAIN)[0]
        self.assertEqual(main_repo, fetched_repo)
        self.assertEqual(main_repo.labels, fetched_repo.labels)
        self.assertEqual(len(fetched_repo.tests_results), 0)

        # delete entry
        dao.delete(repo_url=main_repo.url)
        self.assertEqual([], dao.get_repos_by_tier(Tier.MAIN))

    def test_latest_results(self):
        """Tests append of latest passed test results."""
        dao = DAO(self.path)
        main_repo = get_main_repo()
        dao.write(main_repo)

        dao.add_repo_test_result(
            repo_url=main_repo.url,
            test_result=TestResult(
                passed=True,
                test_type=TestType.STANDARD,
                package=Package.QISKIT,
                package_version="0.18.1",
            ),
        )
        recovered_repo = dao.get_by_url(main_repo.url)
        self.assertEqual(len(recovered_repo.tests_results), 1)

        dao.add_repo_test_result(
            repo_url=main_repo.url,
            test_result=TestResult(
                passed=True,
                test_type=TestType.DEV_COMPATIBLE,
                package=Package.QISKIT,
                package_version="0.18.1",
            ),
        )
        recovered_repo = dao.get_by_url(main_repo.url)
        self.assertEqual(len(recovered_repo.tests_results), 2)

        dao.add_repo_test_result(
            repo_url=main_repo.url,
            test_result=TestResult(
                passed=False,
                test_type=TestType.STABLE_COMPATIBLE,
                package=Package.QISKIT,
                package_version="0.18.1",
            ),
        )
        recovered_repo = dao.get_by_url(main_repo.url)
        self.assertEqual(len(recovered_repo.tests_results), 3)

        # here latest passed should be added
        dao.add_repo_test_result(
            repo_url=main_repo.url,
            test_result=TestResult(
                passed=True,
                test_type=TestType.STABLE_COMPATIBLE,
                package=Package.QISKIT,
                package_version="0.18.1",
            ),
        )
        recovered_repo = dao.get_by_url(main_repo.url)
        self.assertEqual(len(recovered_repo.tests_results), 4)
        self.assertIn(
            TestResult(
                passed=True,
                test_type=TestType.LAST_WORKING_VERSION,
                package=Package.QISKIT,
                package_version="0.18.1",
            ),
            recovered_repo.tests_results,
        )

        # here we check that last passed is updated
        dao.add_repo_test_result(
            repo_url=main_repo.url,
            test_result=TestResult(
                passed=True,
                test_type=TestType.STABLE_COMPATIBLE,
                package=Package.QISKIT,
                package_version="0.20.0",
            ),
        )
        recovered_repo = dao.get_by_url(main_repo.url)
        self.assertEqual(len(recovered_repo.tests_results), 4)
        self.assertIn(
            TestResult(
                passed=True,
                test_type=TestType.LAST_WORKING_VERSION,
                package=Package.QISKIT,
                package_version="0.20.0",
            ),
            recovered_repo.tests_results,
        )

    def test_add_test_result(self):
        """Tests adding result to repo.
        Dao
                -> add_repo_test_result
        """
        dao = DAO(self.path)

        main_repo = get_main_repo()
        dao.write(main_repo)
        dao.add_repo_test_result(
            main_repo.url,
            TestResult(
                passed=False,
                test_type=TestType.DEV_COMPATIBLE,
                package=Package.QISKIT,
                package_version="0.18.1",
            ),
        )
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

        recovered_repo = dao.get_by_url(main_repo.url)
        self.assertEqual(
            recovered_repo.tests_results,
            [
                TestResult(
                    passed=False,
                    test_type=TestType.DEV_COMPATIBLE,
                    package=Package.QISKIT,
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
                    package=Package.QISKIT,
                    package_version="0.18.1",
                )
            ],
        )

        dao.add_repo_test_result(
            main_repo.url,
            TestResult(
                passed=True,
                test_type=TestType.DEV_COMPATIBLE,
                package=Package.QISKIT,
                package_version="0.18.2",
            ),
        )
        dao.add_repo_test_result(
            main_repo.url,
            TestResult(
                passed=False,
                test_type=TestType.STANDARD,
                package=Package.QISKIT,
                package_version="0.18.2",
            ),
        )
        recovered_repo = dao.get_by_url(main_repo.url)
        self.assertEqual(
            recovered_repo.tests_results,
            [
                TestResult(
                    passed=True,
                    test_type=TestType.DEV_COMPATIBLE,
                    package=Package.QISKIT,
                    package_version="0.18.2",
                ),
                TestResult(
                    passed=False,
                    test_type=TestType.STANDARD,
                    package=Package.QISKIT,
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
                    package=Package.QISKIT,
                    package_version="0.18.1",
                ),
                TestResult(
                    passed=True,
                    test_type=TestType.DEV_COMPATIBLE,
                    package=Package.QISKIT,
                    package_version="0.18.2",
                ),
                TestResult(
                    passed=False,
                    test_type=TestType.STANDARD,
                    package=Package.QISKIT,
                    package_version="0.18.2",
                ),
            ],
        )

    def test_add_test_result_order(self):
        """Test order of test results."""
        dao = DAO(self.path)

        main_repo = get_main_repo()
        dao.write(main_repo)
        dao.add_repo_test_result(
            main_repo.url,
            TestResult(
                passed=False,
                test_type=TestType.STABLE_COMPATIBLE,
                package=Package.QISKIT,
                package_version="0.18.1",
            ),
        )
        dao.add_repo_test_result(
            main_repo.url,
            TestResult(
                passed=False,
                test_type=TestType.STANDARD,
                package=Package.QISKIT,
                package_version="0.18.1",
            ),
        )
        dao.add_repo_test_result(
            main_repo.url,
            TestResult(
                passed=False,
                test_type=TestType.DEV_COMPATIBLE,
                package=Package.QISKIT,
                package_version="0.18.1",
            ),
        )

        recovered_repo = dao.get_by_url(main_repo.url)
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
