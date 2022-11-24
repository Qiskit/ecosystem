"""DAO for json db."""
from typing import Optional, List
import os
from collections import OrderedDict
import json

from tinydb import TinyDB, Query

from ecosystem.models import TestResult, StyleResult, CoverageResult, TestType
from ecosystem.models.repository import Repository


class JsonDAO:
    """JsonDAO for repo database."""

    def __init__(self, path: Optional[str] = None):
        """JsonDAO for repository database.

        Args:
            path: path to store database in
        """
        self.path = path if path is not None else os.getcwd()
        self.database = TinyDB("{}/members.json".format(self.path), indent=4)
        self.labels_json_path = os.path.join(self.path, "labels.json")

    def insert(self, repo: Repository) -> int:
        """Inserts repository into database.

        Args:
            repo: Repository

        Return: int
        """
        table = self.database.table(repo.tier)
        self.update_labels(repo.labels)
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

    def update_stars(self, url: str, tier: str, stars: int) -> List[int]:
        """Updates repo with github stars."""
        table = self.database.table(tier)
        return table.update({"stars": stars}, Query().url == url)

    def update_labels(self, labels: List[str]) -> List[int]:
        """Updates labels db."""
        with open(self.labels_json_path, "r") as f:
            label_dscs = {label['name']: label['description'] for label in json.load(f)}

        merged = {**{l: '' for l in labels}, **label_dscs}
        new_label_list = [{'name': name, 'description': dsc} for name, dsc in merged.items()]
        with open(self.labels_json_path, "w") as f:
            json.dump(sorted(new_label_list, key=lambda x: x['name']), f, indent=4)

    def add_repo_test_result(
            self, repo_url: str, tier: str, test_result: TestResult
    ) -> Optional[List[int]]:
        """Adds test result for repository.
        Overwrites the latest test results and adds to historical test results.

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
            repo = Repository.from_dict(fetched_repo_json)

            # add new result and remove old from list
            new_test_results = [
                                   tr for tr in repo.tests_results if
                                   tr.test_type != test_result.test_type
                               ] + [test_result]

            # add last working version
            if (
                    test_result.test_type == TestType.STABLE_COMPATIBLE
                    and test_result.passed
            ):
                last_stable_test_result = TestResult(
                    passed=True,
                    test_type=TestType.LAST_WORKING_VERSION,
                    package=test_result.package,
                    package_version=test_result.package_version,
                    logs_link=test_result.logs_link,
                )
                new_test_results_with_latest = [
                                                   tr
                                                   for tr in new_test_results
                                                   if tr.test_type != last_stable_test_result.test_type
                                               ] + [last_stable_test_result]
                new_test_results = new_test_results_with_latest

            repo.tests_results = sorted(new_test_results, key=lambda r: r.test_type)

            new_historical_est_results = [
                                             tr
                                             for tr in repo.historical_test_results
                                             if tr.test_type != test_result.test_type
                                                or tr.terra_version != test_result.terra_version
                                         ] + [test_result]
            repo.historical_test_results = new_historical_est_results

            return table.upsert(repo.to_dict(), repository.url == repo_url)
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
