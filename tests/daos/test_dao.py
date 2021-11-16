"""Tests for entities."""
import os
from unittest import TestCase
from ecosystem.models import TestResult, TestType, Tier
from ecosystem.daos import JsonDAO
from ecosystem.manager import Manager
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


def get_community_repo() -> Repository:
    """Return main mock repo."""
    return Repository(
        name="mock-qiskit-terra-with-success-dev-test",
        url="https://github.com/MockQiskit/mock-qiskit-wsdt.terra",
        description="Mock description for repo. wsdt",
        licence="Apache 2.0",
        labels=["mock", "tests", "wsdt"],
        tests_results=[TestResult(True, "0.18.1", TestType.DEV_COMPATIBLE)],
        tier=Tier.COMMUNITY,
    )


def get_community_fail_repo() -> Repository:
    """Return main mock repo."""
    return Repository(
        name="mock-qiskit-terra-with-fail-dev-test",
        url="https://github.com/MockQiskit/mock-qiskit-wsdt.terra",
        description="Mock description for repo. wsdt",
        licence="Apache 2.0",
        labels=["mock", "tests", "wsdt"],
        tests_results=[TestResult(False, "0.18.1", TestType.DEV_COMPATIBLE)],
        tier=Tier.COMMUNITY,
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
        """Deletes database file."""
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
        """Tests moving repo from tier to tier."""
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
            destination_tier=Tier.CANDIDATE,
        )
        repos = dao.get_repos_by_tier(Tier.MAIN)
        self.assertEqual(len(repos), 0)

        candidate_repos = dao.get_repos_by_tier(Tier.CANDIDATE)
        self.assertEqual(len(candidate_repos), 1)
        self.assertEqual(candidate_repos[0], moved_repo)

    def test_add_test_result(self):
        """Tests adding result to repo."""
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

        res = dao.add_repo_test_result(
            main_repo.url,
            main_repo.tier,
            TestResult(True, "0.18.2", TestType.DEV_COMPATIBLE),
        )
        self.assertEqual(res, [1])
        recovered_repo = dao.get_by_url(main_repo.url, tier=main_repo.tier)
        self.assertEqual(
            recovered_repo.tests_results,
            [
                TestResult(False, "0.18.1", TestType.DEV_COMPATIBLE),
                TestResult(True, "0.18.2", TestType.DEV_COMPATIBLE),
            ],
        )
        
    def test_update_badges(self):
        """Tests creating badges."""
        self._delete_members_json()

        commu_success = get_community_repo()
        commu_failed = get_community_repo()
        dao = JsonDAO(self.path)

        # insert entry
        dao.insert(commu_success)
        dao.insert(commu_failed)
        
        manager = Manager(root_path=f"{os.path.abspath(os.getcwd())}/..")
        manager.resources_dir = self.path
        manager.dao.path = manager.resources_dir
        
        manager.update_badges()
        
        badges_folder_path = "{}/badges".format(manager.current_dir)
        self.assertTrue(os.path.isfile(f"{badges_folder_path}/{commu_success.name}.svg"))
        self.assertTrue(os.path.isfile(f"{badges_folder_path}/{commu_failed.name}.svg"))
        
        with open(f"{badges_folder_path}/{commu_success.name}.svg", "r") as svg_blueviolet:
            svg_success = svg_blueviolet.read()
        self.assertTrue('fill="blueviolet"' in svg_success)
        
        with open(f"{badges_folder_path}/{commu_failed.name}.svg", "r") as svg_grey:
            svg_failed = svg_grey.read()
        self.assertTrue('fill="blueviolet"' not in svg_failed)
