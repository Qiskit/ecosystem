"""Entrypoint for CLI."""
from typing import Optional, List

from tinydb import TinyDB, Query

from .entities import Repository, Tier, TestResult, StyleResult


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

    def get_all_main(self) -> List[Repository]:
        """Returns all repositories from database."""
        table = self.database.table(Tier.MAIN)
        return [Repository.from_dict(r) for r in table.all()]

    def get_by_url(self, url: str, tier: str) -> Optional[Repository]:
        """Returns repository by URL."""
        res = self.database.table(tier).get(Query().url == url)
        return Repository.from_dict(res) if res else None

    def add_repo_test_result(self, repo_url: str,
                             tier: str,
                             test_result: TestResult) -> Optional[List[int]]:
        """Adds test result for repository."""
        table = self.database.table(tier)
        repository = Query()

        fetched_repo_json = table.get(repository.url == repo_url)
        if fetched_repo_json is not None:
            fetched_repo = Repository.from_dict(fetched_repo_json)
            fetched_test_results = fetched_repo.tests_results

            new_test_results = [tr for tr in fetched_test_results
                                if tr.test_type != test_result.test_type or
                                tr.terra_version != test_result.terra_version] + [test_result]
            fetched_repo.tests_results = new_test_results

            return table.upsert(fetched_repo.to_dict(), repository.url == repo_url)
        return None

    def add_repo_style_result(self, repo_url: str,
                              tier: str,
                              style_result: StyleResult) -> Optional[List[int]]:
        """Adds style result for repository."""
        table = self.database.table(tier)
        repository = Query()

        fetched_repo_json = table.get(repository.url == repo_url)
        if fetched_repo_json is not None:
            fetched_repo = Repository.from_dict(fetched_repo_json)
            fetched_style_results = fetched_repo.styles_results

            new_style_results = [tr for tr in fetched_style_results
                                 if tr.style_type != style_result.style_type] + [style_result]
            fetched_repo.styles_results = new_style_results

            return table.upsert(fetched_repo.to_dict(), repository.url == repo_url)
        return None

    def delete(self, repo: Repository) -> List[int]:
        """Deletes entry."""
        table = self.database.table(repo.tier)
        query = Query()
        return table.remove(query.name == repo.name and query.url == repo.url)
