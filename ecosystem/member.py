"""Submission model."""

import pprint
from uuid import uuid4
import re

from .error_handling import EcosystemError
from .julia import JuliaData
from .serializable import JsonSerializable, parse_datetime
from .github import GitHubData
from .pypi import PyPIData
from .check import CheckData
from .request import URL, request_json
from .validation import validate_member


class Member(JsonSerializable):  # pylint: disable=too-many-instance-attributes
    """main Members class that represent a single entry in the Ecosystem."""

    def __init__(  # pylint: disable=too-many-arguments, too-many-locals
        self,
        name: str,
        submission_number: int | None = None,
        url: str | URL | None = None,
        description: str | None = None,
        licence: str | None = None,
        contact_info: str | None = None,
        affiliations: str | None = None,
        labels: list[str] | None = None,
        interface: list[str] | None = None,
        ibm_maintained: bool = False,
        created_at: int | None = None,
        updated_at: int | None = None,
        website: str | None = None,
        category: str | None = None,
        reference_paper: URL | None = None,
        documentation: URL | None = None,
        packages: list[URL] | None = None,
        uuid: str | None = None,
        badge: str | None = None,
        checks: dict[str, CheckData] | None = None,
        github: GitHubData | None = None,
        pypi: dict[str, PyPIData] | None = None,
        julia: JuliaData | None = None,
    ):
        self.name = name
        self.submission_number = submission_number
        self.url = URL(url) if isinstance(url, str) else url
        self.description = description
        self.licence = licence
        self.contact_info = contact_info
        self.affiliations = affiliations
        self.labels = labels
        self.interface = interface
        self.ibm_maintained = ibm_maintained
        self.created_at = created_at
        self.updated_at = updated_at
        self.website = website
        self.category = category
        self.reference_paper = reference_paper
        self.documentation = documentation
        self.packages = packages
        self.uuid = uuid
        self.github = github
        self.checks = checks or {}
        self.pypi = pypi or {}
        self.julia = julia
        self.badge = badge

        self.__dict__.setdefault("created_at", parse_datetime("now"))
        self.__dict__.setdefault("updated_at", parse_datetime("now"))
        if self.uuid is None:
            self.uuid = str(uuid4())
        if self.labels is None:
            self.labels = []

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
        if "packages" in filtered_dict:
            filtered_dict["packages"] = [URL(p) for p in filtered_dict["packages"]]
        if "checks" in filtered_dict:
            filtered_dict["checks"] = {
                id_: CheckData(id_, **kwargs)
                for id_, kwargs in filtered_dict["checks"].items()
            }
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

    def __str__(self):
        return f"Member({pprint.pformat(self.to_dict(), indent=4)})"

    def __repr__(self):
        return f"Member<{self.name} | {self.url}>"

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
        if self.github:
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
        try:
            response = request_json("https://api-ssl.bitly.com/v4/bitlinks", post=data)
        except EcosystemError as err:
            if "Bad Request (400)" in err.message:
                return None  # Sometimes, bitly errors 400 for some server-side reason
            raise err
        return response["link"]

    def _qisk_dot_it_link_exists(self):
        qisk_dot_it_link_check = request_json(
            f"https://qisk.it/e-{self.short_uuid}",
            parser=lambda x: {"exists": "<title>Qiskit Ecosystem:" in x},
        )
        return (
            f"https://qisk.it/e-{self.short_uuid}"
            if qisk_dot_it_link_check["exists"]
            else None
        )

    def update_badge(self):
        """If not there yet, creates a new Bitly link for the badge"""
        self.badge = self._qisk_dot_it_link_exists()
        if self.badge is None:
            self.badge = self._create_qisk_dot_it_link_for_badge()

    def update_data(self):
        """Update all the member data in each existing section"""
        to_update = [
            "github",
            "pypi",
            "julia",
        ]
        for update_method_str in to_update:
            update_method = getattr(self, f"update_{update_method_str}")
            update_method()

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

    def upsert_sections(self):
        """Create or update sections in a member.
        It is fully local, no validation or internet fetch.
         * github
         * pypi
        """

        # github section
        if not self.github:
            self.github = GitHubData.from_url(self.url)

        # package sections
        if not self.packages:
            self.packages = []

        keep_in_packages = []
        while len(self.packages) > 0:
            package = self.packages.pop(0)
            pypi = PyPIData.from_url(package)
            if pypi:
                self.pypi[pypi.package_name] = pypi
            else:
                keep_in_packages.append(package)

        self.packages = keep_in_packages

    @classmethod
    def from_submission(cls, submission, issue_number: str = None):
        """
        Takes a submission object and creates a very basic Member object
        """
        skip_checks = {}
        if submission.skip:
            for check_id, reason in submission.skip:
                skip_checks[check_id] = CheckData(check_id, xfailed=reason)
        return Member(
            name=submission.name,
            submission_number=issue_number,
            url=submission.source_url,
            description=submission.description,
            contact_info=submission.contact_info,
            labels=submission.labels,
            interface=submission.interface,
            ibm_maintained=submission.is_ibm_maintained,
            website=submission.home_url,
            category=submission.category,
            reference_paper=submission.paper_url,
            documentation=submission.docs_url,
            packages=submission.package_urls,
            checks=skip_checks or None,
        )

    @property
    def xfails(self):
        """list of xfails for a self member"""
        return [
            check
            for checkid, check in self.checks.items()
            if hasattr(check, "xfailed") and check.xfailed
        ]

    def update_checkups(self):
        """Runs validation tests and updates the check-ups sections"""
        checkups = {}
        report = validate_member(self, verbose_level="-q")
        if report.internalerror:
            raise ExceptionGroup(
                "internal error",
                [
                    EcosystemError(
                        f"{internalerror.longreprtext}\n"
                        f"{internalerror.nodeid}\n"
                        f"{internalerror.location[0]}:{internalerror.location[1]}"
                    )
                    for internalerror in report.internalerror
                ],
            )
        for test in report.xfailed + report.failed:
            checkup_data = CheckData.from_report(test)
            checkups[checkup_data.id] = checkup_data
        self.checks = checkups
