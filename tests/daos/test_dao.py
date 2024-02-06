"""Tests for entities."""
import tempfile
import shutil
from pathlib import Path
from unittest import TestCase

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
        self.path = Path(tempfile.mkdtemp())
        self.path.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.path)

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

        # delete entry
        dao.delete(repo_url=main_repo.url)
        self.assertEqual(len(dao.get_all()), 0)
