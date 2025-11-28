"""Tests for entities."""

import tempfile
import shutil
from pathlib import Path
from unittest import TestCase

from ecosystem.dao import DAO
from ecosystem.member import Member


def get_main_repo() -> Member:
    """Return main mock repo."""
    return Member(
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

    def test_repository_insert_and_delete(self):
        """Tests repository."""
        main_repo = get_main_repo()
        dao = DAO(self.path)

        # insert entry
        dao.write(main_repo)
        fetched_repo = dao.get_by_url(str(main_repo.url))
        self.assertEqual(main_repo, fetched_repo)

        # delete entry
        dao.delete(main_repo.name_id)
        dao.refresh_files()
        self.assertEqual(0, len(dao.get_all()))
