"""Submission model."""

import pprint
from uuid import uuid4
import re

from .julia import JuliaData
from .serializable import JsonSerializable, parse_datetime
from .github import GitHubData
from .pypi import PyPIData
from .request import URL, request_json


class Member(JsonSerializable):  # pylint: disable=too-many-instance-attributes
    """main Members class that represent a single entry in the Ecosystem."""

    def __init__(  # pylint: disable=too-many-arguments, too-many-locals
        self,
        name: str,
        url: str | URL | None = None,
        description: str | None = None,
        licence: str | None = None,
        contact_info: str | None = None,
        affiliations: str | None = None,
        labels: list[str] | None = None,
        ibm_maintained: bool = False,
        created_at: int | None = None,
        updated_at: int | None = None,
        website: str | None = None,
        group: str | None = None,
        category: str | None = None,
        reference_paper: URL | None = None,
        documentation: URL | None = None,
        packages: list[URL] | None = None,
        uuid: str | None = None,
        badge: str | None = None,
        github: GitHubData | None = None,
        pypi: dict[str, PyPIData] | None = None,
        julia: JuliaData | None = None,
    ):
        self.name = name
        self.url = URL(url) if isinstance(url, str) else url
        self.description = description
        self.licence = licence
        self.contact_info = contact_info
        self.affiliations = affiliations
        self.labels = labels
        self.ibm_maintained = ibm_maintained
        self.created_at = created_at
        self.updated_at = updated_at
        self.website = website
        self.group = group
        self.category = category
        self.reference_paper = reference_paper
        self.documentation = documentation
        self.packages = packages
        self.uuid = uuid
        self.github = github
        self.pypi = pypi
        self.julia = julia
        self.badge = badge

        self.__dict__.setdefault("created_at", parse_datetime("now"))
        self.__dict__.setdefault("updated_at", parse_datetime("now"))
        if self.github is None:
            self.github = GitHubData.from_url(self.url)
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
        """Transform dictionary to Member.

        Args:
            dictionary: dict object

        Return: Member
        """
        submission_fields = vars(Member)["__static_attributes__"]
        filtered_dict = {k: v for k, v in dictionary.items() if k in submission_fields}
        if "julia" in filtered_dict:
            filtered_dict["julia"] = JuliaData.from_dict(filtered_dict["julia"])
        if "github" in filtered_dict:
            filtered_dict["github"] = GitHubData.from_dict(filtered_dict["github"])
        if "pypi" in filtered_dict:
            for project_name, pypi_dict in filtered_dict["pypi"].items():
                pypi_data = PyPIData.from_dict(
                    {"package_name": project_name} | pypi_dict
                )
                filtered_dict["pypi"][project_name] = pypi_data
        return Member(**filtered_dict)

    def to_dict(self) -> dict:
        base_dict = super().to_dict()
        if "ibm_maintained" in base_dict and base_dict["ibm_maintained"] is False:
            del base_dict["ibm_maintained"]
        return base_dict

    def __eq__(self, other: "Member"):
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
        A unique and human-readable-ish way to identify a submission.
        Remove all non-ASCII chars, lowers the case, and truncates until 10th char.
        Plus short_uuid.

        It is used to create the TOML file name
        """
        flat_name = re.sub("[^A-Za-z0-9]+", "", self.name).lower()[:10]
        return f"{flat_name}_{self.short_uuid}"

    @property
    def badge_md(self):
        """Markdown with the badge for README"""
        return (
            f"[![Qiskit Ecosystem]({self.badge})](https://qisk.it/e)"
            if self.badge
            else None
        )

    def update_github(self):
        """
        Updates all the GitHub information in the project.
        """
        self.github.update_json()
        self.github.update_owner_repo()

    def _create_qisk_dot_it_link_for_badge(self):
        data = {
            "long_url": "https://img.shields.io/endpoint?style=flat&url="
            f"https://qiskit.github.io/ecosystem/b/{self.short_uuid}",
            "domain": "qisk.it",
            "keyword": f"e-{self.short_uuid}",
            "group_guid": "Bj9rgMHKfxH",
            "title": f'Qiskit ecosystem "{self.name}" badge',
            "tags": ["qiskit ecosystem badge", "permanent _do NOT remove_"],
        }
        response = request_json("https://api-ssl.bitly.com/v4/bitlinks", post=data)
        return response["link"]

    def update_badge(self):
        """If not there yet, creates a new Bitly link for the badge"""
        if self.badge is None:
            self.badge = self._create_qisk_dot_it_link_for_badge()

    def update_pypi(self):
        """
        Updates all the PyPI information in the project.
        """
        for package_name in sorted(self.pypi.keys()):
            self.pypi[package_name].update_json()

    def update_julia(self):
        """
        Updates all the Julia information in the project.
        """
        if self.julia:
            self.julia.update_json()

    @classmethod
    def from_submission(cls, submission):
        """
        Takes a submission object and creates a very basic Member object
        """
        return Member(
            name=submission.name,
            url=submission.source_url,
            description=submission.description,
            contact_info=submission.contact_info,
            labels=submission.labels,
            ibm_maintained=submission.is_ibm_maintained,
            website=submission.home_url,
            group=submission.category,
            reference_paper=submission.paper_url,
            documentation=submission.docs_url,
            github=GitHubData.from_url(submission.source_url),
            packages=submission.package_urls,
        )
