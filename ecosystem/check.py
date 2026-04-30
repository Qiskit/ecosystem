"""Checks/Validations section."""

from datetime import datetime
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

    def importance(self, importance_name):
        """Given an importance_name, returns the details"""
        for importance in self._data["importance"]:
            if importance["name"] == importance_name:
                return importance
        raise KeyError("importance name not found")

    def id_by_pytest_node(self, node_id):
        """Given a PyTest node ID, find the test ID"""
        for id_, checkup in self._data.items():
            if not isinstance(checkup, dict):
                continue
            if checkup.get("checker") == node_id:
                return id_
        raise AttributeError(f"nodeid {node_id} not found as a checker")


class CheckData(JsonSerializable):
    """
    The validation data related to a project
    """

    checks_toml = ChecksToml()
    today = datetime.today()

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
    def days_since_failure(self):
        """Returns integer with today-self.since"""
        return (CheckData.today - self.since).days

    @property
    def importance(self):
        """get the importance of the check"""
        if "importance" in self.checks_toml.checkup(self.id):
            return self.checks_toml.checkup(self.id)["importance"]
        return None

    def __repr__(self):
        return str(self.to_dict())

    def __getattr__(self, name):
        return self.checks_toml.checkup(self.id)[name]

    @classmethod
    def from_report(cls, pytest_report):
        """creates a CheckData instance based on a PyTest report"""
        assertion_msg = (
            pytest_report.longreprtext.partition("\n")[0].split(":", 1)[1].strip()
        )
        test_id = cls.checks_toml.id_by_pytest_node(pytest_report.nodeid)
        if hasattr(pytest_report, "wasxfail") and pytest_report.wasxfail:
            return CheckData(
                test_id, details=assertion_msg, xfailed=pytest_report.wasxfail
            )
        since = (
            pytest_report.previously_failed.kwargs["since"]
            if hasattr(pytest_report, "previously_failed")
            else CheckData.today
        )
        return CheckData(test_id, details=assertion_msg, since=since)

    def importances(self):
        """Returns dict name->description with the possible importance values"""
        return {i["name"]: i["description"] for i in self.checks_toml["importance"]}

    def categories(self):
        """Returns dict name->description with the categories"""
        return {i["name"]: i["description"] for i in self.checks_toml["categories"]}

    @property
    def cure_period_in_days(self):
        """The check level cure_period_in_days has precedence over the importance level"""
        cure_period_in_days = None
        importance_level = self.checks_toml.importance(self.importance)
        if "cure_period_in_days" in importance_level:
            cure_period_in_days = importance_level["cure_period_in_days"]
        check_level = self.checks_toml.checkup(self.id)
        if "cure_period_in_days" in check_level:
            cure_period_in_days = check_level["cure_period_in_days"]
        return cure_period_in_days
