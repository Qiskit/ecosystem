"""
DAO for json db.

File structure:

    root_path
    └── members
        └── repo-name.toml
"""

from pathlib import Path
import shutil
import toml

from ecosystem.error_handling import logger, EcosystemError
from ecosystem.member import Member


class TomlStorage:
    """
    Read / write TOML files from a dict where keys are repo URLs, and values
    are Submission objects.

    Can use as a context manager like so:

    with TomlStorage() as data:  # Data is read from TOML files
        data[name_id] = new_repo # Mutate the data
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
            try:
                repo = Member.from_dict(toml.load(path))
            except TypeError as exc:
                raise EcosystemError(f"TOML empty? {path}") from exc
            except toml.decoder.TomlDecodeError as err:
                raise EcosystemError(f"{path} unparsable TOML. {err.args[0]}") from err
            data[path.stem] = repo
        return data

    def refresh_files(self):
        """Forces dumping the DAO to files"""
        # Erase existing TOML files
        # (we erase everything to clean up any deleted repos from data)
        if self.toml_dir.exists():
            shutil.rmtree(self.toml_dir)
        self.write(self._data)

    def write(self, data: dict):
        """
        Dump everything to TOML files from dict of types
        { key (any): repo (Submission) }
        """
        if not self.toml_dir.exists():
            self.toml_dir.mkdir()

        # Write to human-readable TOML
        for submission in data.values():
            submission_dict = submission.to_dict()
            with open(self._name_id_to_path(submission.name_id), "w") as file:
                toml.dump(submission_dict, file)

    def __enter__(self) -> dict:
        if self._data is None:
            self._data = self.read()
        return self._data

    def __exit__(self, _type, _value, exception):
        if _type is not None:
            return False
        self.write(self._data)
        return True


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

    def write(self, repo: Member):
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

    def get_by_url(self, url: str) -> Member:
        """
        Returns project by URL.
        """
        for project in self.get_all():
            if project.url == url:
                return project
        raise EcosystemError(f"No repo with URL : {url}")

    def __getitem__(self, name_id):
        """gets a project by name in the most inefficient way"""
        for project in self.get_all():
            if project.name_id == name_id:
                return project
        raise KeyError(f"No project with name : {name_id}")

    def get_all(self) -> list[Member]:
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
                if isinstance(value, dict):
                    for key, vvalue in value.items():
                        if current_value.get(key, "") != vvalue:
                            logger.info(
                                "Updating %s for %s-%s: %s -> %s",
                                name_id,
                                arg,
                                key,
                                current_value.get(key),
                                str(vvalue),
                            )
                else:
                    if current_value != value:
                        logger.info(
                            "Updating %s for %s: %s -> %s",
                            name_id,
                            arg,
                            current_value,
                            str(value),
                        )
                data[name_id].__dict__[arg] = value

    def refresh_files(self):
        """Forces dumping the DAO to files"""
        self.storage.refresh_files()
