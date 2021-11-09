"""DAO for json db."""
from typing import Optional, List

from tinydb import TinyDB, Query

from ecosystem.models import TestResult, StyleResult, CoverageResult
from ecosystem.models.repository import Repository


class JsonDAO:
    """JsonDAO for repo database."""

    def __init__(self, path: Optional[str] = None):
        """JsonDAO for repository database.

        Args:
            path: path to store database in
        """
        self.path = path if path is not None else "./"
        self.database = TinyDB("{}/members.json".format(self.path), indent=4)

    def insert(self, repo: Repository) -> int:
        """Inserts repository into database.

        Args:
            repo: Repository

        Return: int
        """
        table = self.database.table(repo.tier)
        return table.insert(repo.to_dict())

    def get_repos_by_tier(self, tier: str) -> List[Repository]:
        """Returns all repositories in specified tier.

        Args:
            tier: tier of the repo (MAIN, COMMUNITY, ...)

        Return: Repository
        """
        table = self.database.table(tier)
        return [Repository.from_dict(r) for r in table.all()]

    def delete(self, repo_url: str, tier: str) -> List[int]:
        """Deletes repository from tier.

        Args:
            repo_url: repository url
            tier: tier

        Return: List of int
        """
        table = self.database.table(tier)
        return table.remove(Query().url == repo_url)

    def move_repo_to_other_tier(
        self, repo_url: str, source_tier: str, destination_tier: str
    ) -> Optional[Repository]:
        """Moves repository from one tier to another.

        Args:
            repo_url: URL for repository
            source_tier: source tier of repository
            destination_tier: destination tier

        Returns: Changed repository
        """
        repo = self.get_by_url(url=repo_url, tier=source_tier)
        if repo is not None:
            repo.tier = destination_tier
            is_deleted = self.delete(repo_url=repo_url, tier=source_tier)
            if is_deleted:
                is_inserted = self.insert(repo)
                if is_inserted:
                    return repo
                return None
            return None
        return None

    def get_by_url(self, url: str, tier: str) -> Optional[Repository]:
        """Returns repository by URL.

        Args:
            tier: tier of the repo (MAIN, COMMUNITY, ...)

        Return: Repository
        """
        res = self.database.table(tier).get(Query().url == url)
        return Repository.from_dict(res) if res else None

    def add_repo_test_result(
        self, repo_url: str, tier: str, test_result: TestResult
    ) -> Optional[List[int]]:
        """Adds test result for repository.

        Args:
            repo_url: url of the repo
            tier: tier of the repo (MAIN, COMMUNITY, ...)
            test_result: TestResult from the tox -epy3.x

        Return: List of int
        """
        table = self.database.table(tier)
        repository = Query()

        fetched_repo_json = table.get(repository.url == repo_url)
        if fetched_repo_json is not None:
            fetched_repo = Repository.from_dict(fetched_repo_json)
            fetched_test_results = fetched_repo.tests_results

            new_test_results = [
                tr
                for tr in fetched_test_results
                if tr.test_type != test_result.test_type
                or tr.terra_version != test_result.terra_version
            ] + [test_result]
            fetched_repo.tests_results = new_test_results

            return table.upsert(fetched_repo.to_dict(), repository.url == repo_url)
        return None

    def add_repo_style_result(
        self, repo_url: str, tier: str, style_result: StyleResult
    ) -> Optional[List[int]]:
        """Adds style result for repository.

        Args:
            repo_url: url of the repo
            tier: tier of the repo (MAIN, COMMUNITY, ...)
            style_result: StyleResult from the tox -elint

        Return: List of int
        """
        table = self.database.table(tier)
        repository = Query()

        fetched_repo_json = table.get(repository.url == repo_url)
        if fetched_repo_json is not None:
            fetched_repo = Repository.from_dict(fetched_repo_json)
            fetched_style_results = fetched_repo.styles_results

            new_style_results = [
                tr
                for tr in fetched_style_results
                if tr.style_type != style_result.style_type
            ] + [style_result]
            fetched_repo.styles_results = new_style_results

            return table.upsert(fetched_repo.to_dict(), repository.url == repo_url)
        return None

    def add_repo_coverage_result(
        self, repo_url: str, tier: str, coverage_result: CoverageResult
    ) -> Optional[List[int]]:
        """Adds style result for repository.

        Args:
            repo_url: url of the repo
            tier: tier of the repo (MAIN, COMMUNITY, ...)
            coverage_result: CoverageResult from the tox -ecoverage

        Return: List of int
        """
        table = self.database.table(tier)
        repository = Query()

        fetched_repo_json = table.get(repository.url == repo_url)
        if fetched_repo_json is not None:
            fetched_repo = Repository.from_dict(fetched_repo_json)
            fetched_coverage_results = fetched_repo.coverages_results

            new_coverage_results = [
                tr
                for tr in fetched_coverage_results
                if tr.coverage_type != coverage_result.coverage_type
            ] + [coverage_result]
            fetched_repo.coverages_results = new_coverage_results

            return table.upsert(fetched_repo.to_dict(), repository.url == repo_url)
        return None
