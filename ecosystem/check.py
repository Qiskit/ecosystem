"""Checks/Validations section."""

from pathlib import Path

import tomllib


from .serializable import JsonSerializable


class ChecksToml:
    """handles checks.toml"""

    def __init__(self, toml_filename: str = None, resources_dir: str = None):

        resources_dir = Path(
            resources_dir or Path.joinpath(Path.cwd(), "ecosystem", "resources")
        )
        toml_filename = toml_filename or Path.joinpath(resources_dir, "checks.toml")

        with open(toml_filename, "rb") as f:
            data = tomllib.load(f)
        self._data = data

    def check(self, checkid):
        """Given an ID for a check, the details"""
        return self._data[checkid]


class CheckData(JsonSerializable):
    """
    The validation data related to a project
    """

    dict_keys = ["id", "xfailed", "since", "details"]
    labels_toml = ChecksToml()

    def __init__(self, id_: str, xfailed=None, since=None, details=None):
        self.id = id_
        self.xfailed = xfailed
        self.since = since
        self.details = details

    def __getattr__(self, name):
        return self.labels_toml.check(self.id)[name]

    def importance(self):
        """Returns dict name->description with the possible importance values"""
        return {i["name"]: i["description"] for i in self.labels_toml["importance"]}

    def categories(self):
        """Returns dict name->description with the categories"""
        return {i["name"]: i["description"] for i in self.labels_toml["categories"]}
