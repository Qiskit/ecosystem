"""Submission model."""

from __future__ import annotations

import pprint
from dataclasses import dataclass, fields
from uuid import uuid4
from urllib.parse import urlparse

from .serializable import JsonSerializable, parse_datetime
from .github import GitHubData
from .pypi import PyPIData


@dataclass
class Submission(JsonSerializable):
    """Main project class.

    NOTE: These attribute names must correspond to field IDs in the issue
    template (.github/ISSUE_TEMPLATE/submission.yml).
    """

    # pylint: disable=too-many-instance-attributes
    name: str
    url: str | None = None
    description: str | None = None
    licence: str | None = None
    contact_info: str | None = None
    affiliations: str | None = None
    labels: list[str] | None = None
    ibm_maintained: bool = False
    created_at: int | None = None
    updated_at: int | None = None
    website: str | None = None
    stars: int | None = None
    group: str | None = None
    reference_paper: str | None = None
    documentation: str | None = None
    uuid: str | None = None
    github: GitHubData | None = None
    pypi: dict[str, PyPIData] | None = None

    def __post_init__(self):
        self.__dict__.setdefault("created_at", parse_datetime("now"))
        self.__dict__.setdefault("updated_at", parse_datetime("now"))
        if self.github is None:
            self.github = GitHubData.from_url(urlparse(self.url))
        if self.uuid is None:
            self.uuid = str(uuid4())
        if self.labels is None:
            self.labels = []
        if self.pypi is None:
            self.pypi = {}

    @property
    def short_uuid(self):
        """just the short version of UUID"""
        return self.uuid.split("-")[0]

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Transform dictionary to Submission.

        Args:
            dictionary: dict object

        Return: Submission
        """
        submission_fields = [f.name for f in fields(Submission)]
        filtered_dict = {k: v for k, v in dictionary.items() if k in submission_fields}
        if "github" in filtered_dict:
            filtered_dict["github"] = GitHubData.from_dict(filtered_dict["github"])
        if "pypi" in filtered_dict:
            for project_name, pypi_dict in filtered_dict["pypi"].items():
                pypi_data = PyPIData.from_dict(
                    {"package_name": project_name} | pypi_dict
                )
                filtered_dict["pypi"][project_name] = pypi_data
        return Submission(**filtered_dict)

    def to_dict(self) -> dict:
        base_dict = super().to_dict()
        base_dict["badge"] = (
            "[![Qiskit Ecosystem](https://img.shields.io/endpoint?style=flat&url=https"
            f"%3A%2F%2Fqiskit.github.io%2Fecosystem%2Fb%2F{self.short_uuid})]"
            "(https://qisk.it/e)"
        )
        return base_dict

    def __eq__(self, other: "Submission"):
        return (
            self.url == other.url
            and self.description == other.description
            and self.licence == other.licence
        )

    def __repr__(self):
        return pprint.pformat(self.to_dict(), indent=4)

    def __str__(self):
        return f"Submission({self.name} | {self.url})"

    @property
    def name_id(self):
        """
        A unique and human-readable way to identify a submission
        It is used to create the TOML file name
        """
        # TODO: it is not uniq tho. Maybe add a random number at the end?  pylint: disable=W0511
        return self.url.strip("/").split("/")[-1]

    def update_github(self):
        """
        Updates all the GitHub information in the project.
        """
        self.github.update_json()
        self.github.update_owner_repo()

    def update_pypi(self):
        """
        Updates all the PyPI information in the project.
        """
        for package_name in sorted(self.pypi.keys()):
            self.pypi[package_name].update_json()
