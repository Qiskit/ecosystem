"""Checks/Validations section."""

import datetime
from pathlib import Path

import tomllib


from .serializable import JsonSerializable
from .request import URL


class ChecksToml:
    """handles checks.toml"""

    def __init__(self, toml_filename: str = None, resources_dir: str = None):
        resources_dir = Path(resources_dir or Path.joinpath(Path.cwd(), "resources"))
        toml_filename = toml_filename or Path.joinpath(resources_dir, "checks.toml")

        with open(toml_filename, "rb") as f:
            data = tomllib.load(f)
        self._data = data

    def checkup(self, checkup_id):
        """Given an ID for a check, the details"""
        return self._data[checkup_id]

    def id_by_pytest_node(self, node_id):
        """Given a PyTest node ID, find the test ID"""
        for id_, checkup in self._data.items():
            if not isinstance(checkup, dict):
                continue
            if checkup.get("checker") == node_id:
                return id_
        raise AttributeError(f"nodeid {node_id} not found")


class CheckData(JsonSerializable):
    """
    The validation data related to a project
    """

    labels_toml = ChecksToml()

    def __init__(
        self, id_: str, xfailed=None, since=None, details=None, discussion=None, **_
    ):
        self.id = id_
        self.xfailed = xfailed
        self.since = since
        self.details = details
        self.discussion: str | URL | None = discussion

    def to_dict(self) -> dict:
        ret = super().to_dict()
        del ret["id"]
        ret["importance"] = self.importance
        return ret

    @property
    def importance(self):
        """get the importance of the check"""
        if "importance" in self.labels_toml.checkup(self.id):
            return self.labels_toml.checkup(self.id)["importance"]
        return None

    def __repr__(self):
        return str(self.to_dict())

    def __getattr__(self, name):
        return self.labels_toml.checkup(self.id)[name]

    @classmethod
    def from_report(cls, pytest_report):
        """creates a CheckData instance based on a PyTest report"""
        assertion_msg = (
            pytest_report.longreprtext.partition("\n")[0].split(":", 1)[1].strip()
        )
        test_id = cls.labels_toml.id_by_pytest_node(pytest_report.nodeid)
        if hasattr(pytest_report, "wasxfail") and pytest_report.wasxfail:
            return CheckData(
                test_id, details=assertion_msg, xfailed=pytest_report.wasxfail
            )
        since = (
            pytest_report.previously_failed.kwargs["since"]
            if hasattr(pytest_report, "previously_failed")
            else datetime.datetime.today()
        )
        return CheckData(test_id, details=assertion_msg, since=since)

    def importances(self):
        """Returns dict name->description with the possible importance values"""
        return {i["name"]: i["description"] for i in self.labels_toml["importance"]}

    def categories(self):
        """Returns dict name->description with the category_names"""
        return {i["name"]: i["description"] for i in self.labels_toml["category_names"]}
