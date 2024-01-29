"""
DAO for json db.

File structure:

    root_path
    └── members
        └── repo-name.toml
"""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import toml

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

    def write(self, repo: Repository):
        """
        Update or insert repo (identified by URL).
        """
        self.update_labels(repo.labels)
        with self.storage as data:
            data[repo.url] = repo

    def delete(self, repo_url: str):
        """Deletes repository from database.

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

    def get_all(self) -> list[Repository]:
        """
        Returns list of all repositories.
        """
        return self.storage.read().values()

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
