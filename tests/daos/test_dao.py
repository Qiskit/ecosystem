"""Tests for entities."""
import os
import shutil
import json
from unittest import TestCase
from pathlib import Path

from ecosystem.daos import DAO
from ecosystem.models.repository import Repository


def get_main_repo() -> Repository:
    """Return main mock repo."""
    return Repository(
        name="mock-qiskit-terra-with-success-dev-test",
        url="https://github.com/MockQiskit/mock-qiskit-wsdt.terra",
        description="Mock description for repo. wsdt",
        licence="Apache 2.0",
        labels=["mock", "tests", "wsdt"],
        website="https://example.org",
    )


class TestDao(TestCase):
    """Tests repository related functions."""

    def setUp(self) -> None:
        self.path = "../resources"
        self.labels_path = "{}/labels.json".format(self.path)
        self._create_dummy_labels_json()
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def _delete_labels_json(self):
        """Deletes labels file.
        Function: Dao
                -> delete
        """
        if os.path.exists(self.labels_path):
            os.remove(self.labels_path)
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def test_stars_update(self):
        """Test update stars for repo."""
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
        fetched_repo = dao.get_by_url(main_repo.url)
        self.assertEqual(main_repo, fetched_repo)
        self.assertEqual(main_repo.labels, fetched_repo.labels)

        # delete entry
        dao.delete(repo_url=main_repo.url)
        self.assertEqual(len(dao.get_all()), 0)

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
