# This code is part of Qiskit.
#
# (C) Copyright IBM 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Checks/Validations section."""

import os
from datetime import date, timedelta
from pathlib import Path

import tomllib
from slugify import slugify


from .error_handling import EcosystemError
from .serializable import JsonSerializable, parse_date
from .request import URL, request_json


def parse_exclusions(exclude) -> set[str]:
    """The `exclude` argument of the CLI commands, as a set of slugs.

    Fire hands over a tuple for `-e "a, b"` and a plain string for a single `-e a`, and the
    values are slugified, so `-e BEST-PRACTICE`, `-e best_practice` and `-e "Best Practice"`
    all name the same thing."""
    if exclude is None:
        return set()
    if isinstance(exclude, str):
        exclude = [exclude]
    return {slugify(str(value)) for value in exclude}


class ChecksToml:
    """handles checks.toml"""

    def __init__(self, toml_filename: str = None, resources_dir: str = None):
        env_resources_dir = os.getenv("ECOSYSTEM_RESOURCES_DIR")
        resources_dir = Path(
            resources_dir or env_resources_dir or (Path.cwd() / "resources")
        )

        toml_filename = toml_filename or Path.joinpath(resources_dir, "checks.toml")

        with open(toml_filename, "rb") as f:
            data = tomllib.load(f)
        self._data = data

    @property
    def checkups(self):
        """Every check up in checks.toml, as a dict id -> details"""
        # the `importance` and `categories` entries are lists of definitions, not check ups
        return {
            id_: checkup
            for id_, checkup in self._data.items()
            if isinstance(checkup, dict)
        }

    def cure_period(self, checkup_id):
        """The cure period of a check up, in days.

        The cure period is a property of the check up. When the check up does not state one,
        the default of its importance level applies."""
        checkup = self.checkup(checkup_id)
        if "cure_period_in_days" in checkup:
            return checkup["cure_period_in_days"]
        return self.importance(checkup["importance"]).get("cure_period_in_days")

    @property
    def importances(self):
        """The importance levels, from the most to the least severe"""
        return self._data["importance"]

    @property
    def categories(self):
        """The check up categories"""
        return self._data["categories"]

    def checkup(self, checkup_id):
        """Given an ID for a check, the details"""
        return self._data[checkup_id]

    def importance(self, importance_name):
        """Given an importance_name, returns the details"""
        for importance in self._data["importance"]:
            if importance["name"] == importance_name:
                return importance
        raise KeyError("importance name not found")

    def importance_rank(self, importance_name):
        """Where an importance sits among the levels, 0 being the most severe.

        The order is the order of the `[[importance]]` entries in checks.toml. A name that is
        not one of them sorts last."""
        names = [importance["name"] for importance in self.importances]
        if importance_name in names:
            return names.index(importance_name)
        return len(names)

    def id_by_pytest_node(self, node_id):
        """Given a PyTest node ID, find the test ID"""
        for id_, checkup in self.checkups.items():
            if checkup.get("checker") == node_id:
                return id_
        raise AttributeError(f"nodeid {node_id} not found as a checker")

    def category_by_pytest_node(self, node_id):
        """Given a PyTest node ID, find the category"""
        return self.checkup(self.id_by_pytest_node(node_id))["category"]

    def importance_by_pytest_node(self, node_id):
        """Given a PyTest node ID, find the importance"""
        return self.checkup(self.id_by_pytest_node(node_id))["importance"]


class CheckData(JsonSerializable):
    """
    The validation data related to a project
    """

    checks_toml = ChecksToml()
    today = date.today()

    def __init__(  # pylint: disable=too-many-arguments
        self,
        id_: str,
        xfailed=None,
        xfailed_until=None,
        since=None,
        source=None,
        details=None,
        discussion=None,
        **_,
    ):
        self.id = id_
        self.xfailed = xfailed
        self.xfailed_until = parse_date(xfailed_until)
        self.since = parse_date(since)
        self.source: str | None = source
        self.details = details
        self.discussion: str | URL | None = discussion

    def to_dict(self, keys=None) -> dict:
        ret = super().to_dict(keys=keys)
        del ret["id"]
        ret["importance"] = self.importance
        return ret

    @property
    def days_since_failure(self):
        """Returns integer with today-self.since"""
        return (CheckData.today - self.since).days

    @property
    def xfailed_expired(self):
        """True if `self.xfailed_until` is in the past.

        An `self.xfailed` explanation without `self.xfailed_until` never expires."""
        if self.xfailed_until is None:
            return False
        return CheckData.today > self.xfailed_until

    @property
    def xfail_applies(self):
        """True if there is an explanation for the failure and it has not expired yet.

        This is the question to ask before honoring `self.xfailed`: an expired explanation
        does not excuse the check up anymore."""
        return bool(self.xfailed) and not self.xfailed_expired

    @property
    def days_until_xfailed_expires(self):
        """Days left before `self.xfailed` stops applying.
        None if the explanation does not expire."""
        if self.xfailed_until is None:
            return None
        return (self.xfailed_until - CheckData.today).days

    @property
    def importance(self):
        """get the importance of the check"""
        if "importance" in self.checks_toml.checkup(self.id):
            return self.checks_toml.checkup(self.id)["importance"]
        return None

    @property
    def importance_rank(self):
        """Where the importance of the check up sits among the levels, 0 being the most
        severe. See `ChecksToml.importance_rank`"""
        return self.checks_toml.importance_rank(self.importance)

    @property
    def importance_icon(self):
        """Returns the icon for the checkup importance level or None if none defined"""
        if "icon" in self.checks_toml.importance(self.importance):
            return self.checks_toml.importance(self.importance)["icon"]
        return None

    @property
    def importance_description(self):
        """Returns the description for the checkup importance level or None if none defined"""
        if "description" in self.checks_toml.importance(self.importance):
            return self.checks_toml.importance(self.importance)["description"]
        return None

    def __repr__(self):
        return str(self.to_dict())

    def __getattr__(self, name):
        try:
            return self.checks_toml.checkup(self.id)[name]
        except KeyError as key_error:
            # so getattr(checkdata, name, default) and hasattr work as expected
            raise AttributeError(f"the check up {self.id} has no {name}") from key_error

    @property
    def source_api_url(self):
        """`self.source` (a GitHub issue URL) as the GitHub API URL of that issue"""
        url = URL(self.source)
        path = url.path.strip("/").split("/")
        if (
            url.hostname != "github.com"
            or len(path) != 4
            or path[2] not in ["issues", "pull"]
        ):
            raise EcosystemError(
                f"the source of the check up {self.id} does not look like "
                f"a GitHub issue: {self.source}"
            )
        owner, repo, _, number = path
        return f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"

    def update_from_source(self):
        """Updates the check up with the state of the issue in `self.source`.

        A source-based check up is not the result of a test: it exists because there is an
        issue that is not getting closed as complete. So, instead of running a checker, the
        state of that issue is checked. If the issue is closed, the reason is added to
        `self.details`, so a human can decide what to do with the check up.

        The check up itself is never removed here: a closed issue does not necessarily mean
        that the situation described in `self.details` is solved.
        """
        # what is added to self.details when the check up source issue is closed
        source_closed_details = {
            "completed": "the source issue is closed as completed",
            "not_planned": "the source issue is closed as not planned",
            None: "the source issue is closed",
        }
        if not self.source:
            return
        issue = request_json(self.source_api_url)
        annotation = None
        if issue["state"] != "open":
            annotation = source_closed_details.get(
                issue.get("state_reason"), source_closed_details[None]
            )
        details = self.details or ""
        for known_annotation in source_closed_details.values():
            # drop a previous annotation, so they do not pile up on every run
            # and they do not survive the issue being reopened
            details = details.replace(f" ({known_annotation})", "")
        if annotation:
            details = f"{details} ({annotation})".strip()
        self.details = details or None

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
        return {i["name"]: i["description"] for i in self.checks_toml.importances}

    def categories(self):
        """Returns dict name->description with the categories"""
        return {i["name"]: i["description"] for i in self.checks_toml.categories}

    @property
    def cure_period_in_days(self):
        """The cure period of the check up, in days. See `ChecksToml.cure_period`"""
        return self.checks_toml.cure_period(self.id)

    @property
    def cure_period_is_infinite(self):
        """True if the cure period never runs out.

        A negative `cure_period_in_days` (by convention, `-1`) means an infinite cure period:
        the check up keeps being pending, but it never becomes a reason to retire the project.
        To keep a check up from counting towards the membership status at all, exclude its
        importance or its category instead (see `CliMembers.update_status`).
        """
        if self.cure_period_in_days is None:
            return False
        return self.cure_period_in_days < 0

    @property
    def cure_period_deadline(self):
        """The last day the check up can be failing before the project has to be retired.
        None if the cure period never runs out (see `self.cure_period_is_infinite`)."""
        if self.cure_period_is_infinite or self.since is None:
            return None
        return self.since + timedelta(days=self.cure_period_in_days)

    @property
    def days_left_in_cure_period(self):
        """Days left before there is no time to fix the check up anymore. Negative once the
        deadline is behind (which only retires the project if its importance is not excluded).

        None when there is no deadline to count towards: an infinite cure period (see
        `self.cure_period_is_infinite`) or no `self.since` to count from."""
        if self.cure_period_is_infinite or self.since is None:
            return None
        return self.cure_period_in_days - self.days_since_failure

    @property
    def cure_period_expired(self):
        """True if there is no time left to fix the check up."""
        if self.cure_period_deadline is None:
            return False
        return CheckData.today > self.cure_period_deadline
