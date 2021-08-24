"""Entrypoint for CLI."""
from typing import Optional, List

from tinydb import TinyDB, Query, where

from .entities import Repository, MainRepository, Tier


class Controller:
    """Controller for repo database."""

    def __init__(self, path: Optional[str] = None):
        """Controller for repository database.

        Args:
            path: path to store database in
        """
        self.path = path if path is not None else "./"
        self.database = TinyDB('{}/members.json'.format(self.path), indent=4)

    def insert(self, repo: Repository) -> int:
        """Inserts repository into database."""
        table = self.database.table(repo.tier)
        return table.insert(repo.to_dict())

    def get_all_main(self) -> List[MainRepository]:
        """Returns all repositories from database."""
        table = self.database.table(Tier.MAIN)
        return [MainRepository(**r) for r in table.all()]

    def get_by_url(self, url: str, tier: str) -> Optional[Repository]:
        """Returns repository by URL."""
        res = self.database.table(tier).get(Query().url == url)
        return MainRepository(**res) if res else None

    def update_repo_tests_passed(self, repo: Repository,
                                 tests_passed: List[str]) -> List[int]:
        """Updates repository passed tests."""
        table = self.database.table(repo.tier)
        return table.update({"tests_passed": tests_passed},
                            where('name') == repo.name)

    def add_repo_test_passed(self,
                             repo_url: str,
                             test_passed: str,
                             tier: str):
        """Adds passed test if is not there yet."""
        table = self.database.table(tier)
        repo = self.get_by_url(repo_url, tier)
        if repo:
            tests_passed = repo.tests_passed
            if test_passed not in tests_passed:
                tests_passed.append(test_passed)
                return table.update({"tests_passed": tests_passed},
                                    where('name') == repo.name)
        return [0]

    def remove_repo_test_passed(self,
                                repo_url: str,
                                test_remove: str,
                                tier: str):
        """Remove passed tests."""
        table = self.database.table(tier)
        repo = self.get_by_url(repo_url, tier)
        if repo:
            tests_passed = repo.tests_passed
            if test_remove in tests_passed:
                tests_passed.remove(test_remove)
                return table.update({"tests_passed": tests_passed},
                                    where('name') == repo.name)
        return [0]

    def delete(self, repo: Repository) -> List[int]:
        """Deletes entry."""
        table = self.database.table(repo.tier)
        query = Query()
        return table.remove(query.name == repo.name and query.url == repo.url)
