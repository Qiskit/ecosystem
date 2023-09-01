"""
DAO for json db.

File structure:

    root_path
    ├── members.json  # compiled file; don't edit manually
    └── members
        └── repo-name.toml
"""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import toml

from ecosystem.utils import logger
from ecosystem.models import TestResult, StyleResult, CoverageResult, TestType
from ecosystem.models.repository import Repository


class TomlStorage:
    """
    Read / write TOML files from a dict where keys are repo URLs, and values
    are Repository objects.

    Can use as a context manager like so:

    with TomlStorage() as data:  # Data is read from TOML files
        data[url] = new_repo     # Mutate the data
                                 # Changes are saved on exit
    """

    def __init__(self, root_path: str):
        self.toml_dir = Path(root_path, "members")
        self._data = None  # for use with context manager

    def _url_to_path(self, url):
        repo_name = url.strip("/").split("/")[-1]
        return self.toml_dir / f"{repo_name}.toml"

    def read(self) -> dict:
        """
        Search for TOML files and read into dict with types:
        { url (str): repo (Repository) }
        """
        data = {}
        for path in self.toml_dir.glob("*"):
            repo = Repository.from_dict(toml.load(path))
            data[repo.url] = repo
        return data

    def write(self, data: dict):
        """
        Dump everything to TOML files from dict of types
        { key (any): repo (Repository) }
        """
        # Erase existing TOML files
        # (we erase everything to clean up any deleted repos)
        if self.toml_dir.exists():
            shutil.rmtree(self.toml_dir)

        # Write to human-readable TOML
        self.toml_dir.mkdir()
        for repo in data.values():
            with open(self._url_to_path(repo.url), "w") as file:
                toml.dump(repo.to_dict(), file)

    def __enter__(self) -> dict:
        self._data = self.read()
        return self._data

    def __exit__(self, _type, _value, exception):
        if exception is not None:
            raise exception
        self.write(self._data)


class DAO:
    """
    Data access object for repository database.
    """

    def __init__(self, path: str):
        """
        Args:
            path: path to store database in
        """
        self.storage = TomlStorage(path)
        self.labels_json_path = Path(path, "labels.json")
        self.compiled_json_path = Path(path, "members.json")

    def write(self, repo: Repository):
        """
        Update or insert repo (identified by URL).
        """
        self.update_labels(repo.labels)
        with self.storage as data:
            data[repo.url] = repo

    def get_repos_by_tier(self, tier: str) -> list[Repository]:
        """
        Returns all repositories in specified tier.

        Args:
            tier: tier of the repo (MAIN, COMMUNITY, ...)
        """
        matches = [repo for repo in self.storage.read().values() if repo.tier == tier]
        return matches

    def delete(self, repo_url: str):
        """Deletes repository from tier.

        Args:
            repo_url: repository url
        """
        with self.storage as data:
            del data[repo_url]

    def get_by_url(self, url: str) -> Repository | None:
        """
        Returns repository by URL.
        """
        data = self.storage.read()
        if url not in data:
            logger.info("No repo with URL : %s", url)
            return None
        return self.storage.read()[url]

    def update(self, repo_url: str, **kwargs):
        """
        Update attributes of repository.

        Args:
            repo_url (str): URL of repo
            kwargs: Names of attributes and new values

        Example usage:
            update("github.com/qiskit/qiskit, name="qiskit", stars=300)
        """
        with self.storage as data:
            for arg, value in kwargs.items():
                data[repo_url].__dict__[arg] = value

    def update_labels(self, labels: list[str]):
        """
        Updates labels file for consumption by qiskit.org.
        """
        with open(self.labels_json_path, "r") as labels_file:
            existing_labels = {
                label["name"]: label["description"] for label in json.load(labels_file)
            }

        merged = {**{l: "" for l in labels}, **existing_labels}
        new_label_list = [
            {"name": name, "description": dsc} for name, dsc in merged.items()
        ]
        with open(self.labels_json_path, "w") as labels_file:
            json.dump(
                sorted(new_label_list, key=lambda x: x["name"]), labels_file, indent=4
            )

    def compile_json(self):
        """
        Dump database to JSON file for consumption by qiskit.org
        Needs this structure:

        { tier: {  # e.g. Main, Community
            index: repo  # `repo` is data from repo-name.toml
        }}

        """
        data = self.storage.read()

        out = {}
        for repo in data.values():
            if repo.tier not in out:
                out[repo.tier] = {}
            index = str(len(out[repo.tier]))
            out[repo.tier][index] = repo.to_dict()

        with open(self.compiled_json_path, "w") as file:
            json.dump(out, file, indent=4)

    def add_repo_test_result(self, repo_url: str, test_result: TestResult) -> None:
        """
        Adds test result to repository.
        Overwrites the latest test results and adds to historical test results.

        Args:
            repo_url: url of the repo
            test_result: TestResult from the tox -epy3.x
        """
        repo = self.get_by_url(repo_url)

        if repo is None:
            return None

        # add new result and remove old from list
        new_test_results = [
            tr for tr in repo.tests_results if tr.test_type != test_result.test_type
        ] + [test_result]

        # add last working version
        if test_result.test_type == TestType.STABLE_COMPATIBLE and test_result.passed:
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

        new_historical_test_results = [
            tr
            for tr in repo.historical_test_results
            if tr.test_type != test_result.test_type
            or tr.qiskit_version != test_result.qiskit_version
        ] + [test_result]
        repo.historical_test_results = new_historical_test_results
        self.write(repo)
        return None

    def add_repo_style_result(self, repo_url: str, style_result: StyleResult) -> None:
        """
        Adds style result for repository.

        Args:
            repo_url: url of the repo
            style_result: StyleResult from the tox -elint
        """
        repo = self.get_by_url(repo_url)

        if repo is None:
            return None

        new_style_results = [
            tr for tr in repo.styles_results if tr.style_type != style_result.style_type
        ] + [style_result]
        repo.styles_results = new_style_results
        self.write(repo)
        return None

    def add_repo_coverage_result(
        self, repo_url: str, coverage_result: CoverageResult
    ) -> None:
        """
        Adds coverage result for repository.

        Args:
            repo_url: url of the repo
            coverage_result: CoverageResult from the tox -ecoverage
        """
        repo = self.get_by_url(repo_url)

        if repo is None:
            return None

        new_coverage_results = [
            tr
            for tr in repo.coverages_results
            if tr.coverage_type != coverage_result.coverage_type
        ] + [coverage_result]
        repo.coverages_results = new_coverage_results
        self.write(repo)
        return None
