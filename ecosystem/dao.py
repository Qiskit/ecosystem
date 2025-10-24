"""
DAO for json db.

File structure:

    root_path
    └── members
        └── repo-name.toml
"""

# from __future__ import annotations
from pathlib import Path
import shutil
import toml

from ecosystem.error_handling import logger, EcosystemError
from ecosystem.submission import Submission


class TomlStorage:
    """
    Read / write TOML files from a dict where keys are repo URLs, and values
    are Submission objects.

    Can use as a context manager like so:

    with TomlStorage() as data:  # Data is read from TOML files
        data[url] = new_repo     # Mutate the data
                                 # Changes are saved on exit
    """

    def __init__(self, root_path: str):
        self.toml_dir = Path(root_path, "members")
        self._data = None  # for use with context manager

    def _name_id_to_path(self, name_id):
        return self.toml_dir / f"{name_id}.toml"

    def read(self) -> dict:
        """
        Search for TOML files and read into dict with types:
        { url (str): repo (Submission) }
        """
        data = {}
        for path in self.toml_dir.glob("*.toml"):
            repo = Submission.from_dict(toml.load(path))
            data[path.stem] = repo
        return data

    def write(self, data: dict):
        """
        Dump everything to TOML files from dict of types
        { key (any): repo (Submission) }
        """
        # Erase existing TOML files
        # (we erase everything to clean up any deleted repos)
        if self.toml_dir.exists():
            shutil.rmtree(self.toml_dir)

        # Write to human-readable TOML
        self.toml_dir.mkdir()
        for submission in data.values():
            with open(self._name_id_to_path(submission.name_id), "w") as file:
                submission_dict = submission.to_dict()
                toml.dump(submission_dict, file)

    def __enter__(self) -> dict:
        self._data = self.read()
        return self._data

    def __exit__(self, _type, _value, exception):
        if _type is not None:
            return False
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

    def write(self, repo: Submission):
        """
        Update or insert repo (identified by ID).
        """
        with self.storage as data:
            data[repo.name_id] = repo

    def delete(self, name_id: str = None):
        """Deletes repository from database.

        Args:
            name_id: ID of the project. Typically, the name of the TOML file
        """
        with self.storage as data:
            del data[name_id]

    def get_by_url(self, url: str) -> Submission:
        """
        Returns project by URL.
        """
        for project in self.get_all():
            if project.url == url:
                return project
        raise ValueError(f"No repo with URL : {url}")

    def get_all(self) -> list[Submission]:
        """
        Returns list of all repositories.
        """
        return self.storage.read().values()

    def update(self, name_id: str = None, **kwargs):
        """
        Update attributes of repository.

        Args:
            name_id (str): ID of the project. Typically, name of the TOML file.
            kwargs: Names of attributes and new values

        Example usage:
            update("qiskit-aer", stars=300)
        """
        with self.storage as data:
            for arg, value in kwargs.items():
                current_value = data[name_id].__dict__.get(arg)
                if current_value != value:
                    logger.info(
                        "Updating %s for %s: %s -> %s",
                        name_id,
                        arg,
                        current_value,
                        str(value),
                    )
                data[name_id].__dict__[arg] = value
