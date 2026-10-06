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

"""Submission model."""

import pprint
from datetime import date
from uuid import uuid4
from dateutil.relativedelta import relativedelta
from packaging.utils import canonicalize_name
from slugify import slugify

from .error_handling import EcosystemError
from .julia import JuliaData
from .license import License
from .serializable import JsonSerializable, parse_date
from .github import GitHubData
from .pypi import PyPIData
from .python import PythonData
from .requirements import RequirementsData
from .check import CheckData
from .cargo import CargoData
from .crates import CratesData
from .badge import BadgeData
from .request import URL
from .validation import validate_member


class Member(  # pylint: disable=too-many-instance-attributes,too-many-public-methods
    JsonSerializable
):
    """main Members class that represent a single entry in the Ecosystem."""

    # How long an explanation for a failing check up (`check.xfailed`) coming from a
    # submission is valid for. After that, the check up is verified again as a regular one.
    DEFAULT_XFAILED_PERIOD_IN_MONTHS = 12

    def __init__(  # pylint: disable=too-many-arguments, too-many-locals
        self,
        name: str,
        submission_number: int | None = None,
        url: str | URL | None = None,
        description: str | None = None,
        license: License | None = None,  # pylint: disable=redefined-builtin
        contact_info: str | None = None,
        affiliations: str | None = None,
        labels: list[str] | None = None,
        interfaces: list[str] | None = None,
        ibm_maintained: bool = False,
        created_at: int | None = None,
        updated_at: int | None = None,
        website: str | None = None,
        category: str | None = None,
        reference_paper: URL | None = None,
        documentation: URL | None = None,
        packages: list[URL] | None = None,
        uuid: str | None = None,
        badge: str | BadgeData = None,
        checks: dict[str, CheckData] | None = None,
        github: GitHubData | None = None,
        pypi: list[PyPIData] | None = None,
        crates: list[CratesData] | None = None,
        cargo: list[CargoData] | None = None,
        julia: list[JuliaData] | None = None,
        python: list[PythonData] | None = None,
        requirements: list[RequirementsData] | None = None,
        maturity: str | None = None,
        status: str | None = None,
    ):
        self._filename = None
        self.name = name
        self.submission_number = submission_number
        self.url = URL(url) if isinstance(url, str) else url
        self.description = description
        self.license = (
            License(license, where="user") if isinstance(license, str) else license
        )
        self.contact_info = contact_info
        self.affiliations = affiliations
        self.labels = labels
        self.interfaces = interfaces
        self.ibm_maintained = ibm_maintained
        self.created_at = created_at
        self.updated_at = updated_at
        self.website = URL(website) if isinstance(website, str) else website
        self.category = category
        self.reference_paper = (
            URL(reference_paper)
            if isinstance(reference_paper, str)
            else reference_paper
        )
        self.documentation = (
            URL(documentation) if isinstance(documentation, str) else documentation
        )
        self.packages = packages
        self.uuid = uuid
        self.github = github
        self.checks = checks or {}
        # arrays of tables, like `requirements`: what identifies an entry is its own
        # `package_name`, which every one of them stores anyway
        self.pypi = pypi or []
        self.crates = crates or []
        self.cargo = cargo or []
        self.julia = julia or []
        self.python = python or []
        self.requirements = requirements
        self.badge = badge
        self.maturity = maturity
        self.status = status

        self.__dict__.setdefault("created_at", parse_date("now"))
        self.__dict__.setdefault("updated_at", parse_date("now"))
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

        if "badge" in filtered_dict:
            filtered_dict["badge"] = (
                BadgeData(url=filtered_dict["badge"])
                if isinstance(filtered_dict["badge"], str)
                else BadgeData.from_dict(filtered_dict["badge"])
            )

        if "github" in filtered_dict:
            filtered_dict["github"] = GitHubData.from_dict(filtered_dict["github"])

        if "requirements" in filtered_dict:
            filtered_dict["requirements"] = [
                RequirementsData.from_dict(requirements_dict)
                for requirements_dict in filtered_dict["requirements"]
            ]

        for section, data_class in (
            ("pypi", PyPIData),
            ("crates", CratesData),
            ("cargo", CargoData),
            ("julia", JuliaData),
            ("python", PythonData),
        ):
            if section in filtered_dict:
                filtered_dict[section] = [
                    data_class.from_dict(table) for table in filtered_dict[section]
                ]
        if "packages" in filtered_dict:
            filtered_dict["packages"] = [URL(p) for p in filtered_dict["packages"]]
        if "checks" in filtered_dict:
            # keyed arrays of tables: the id is still the identity, and it is looked up by
            # it, but a check up that reads several places has a record per failing place
            filtered_dict["checks"] = {
                id_: [CheckData(id_, **table) for table in tables]
                for id_, tables in filtered_dict["checks"].items()
            }
        if "license" in filtered_dict and filtered_dict["license"] is not None:
            filtered_dict["license"] = License(filtered_dict["license"], where="user")
        return Member(**filtered_dict)

    #: The sections that are arrays of tables, keyed by nothing: an entry carries the name
    #: of what it describes
    ARRAY_SECTIONS = ("pypi", "crates", "cargo", "julia", "python", "requirements")

    def to_dict(self, keys=None) -> dict:
        base_dict = super().to_dict(keys=keys)
        if "ibm_maintained" in base_dict and base_dict["ibm_maintained"] is False:
            del base_dict["ibm_maintained"]
        # a member with no distributions has no `pypi = []` line: `to_dict` drops an empty
        # dict but keeps an empty list, which only showed once these sections became arrays
        for section in self.ARRAY_SECTIONS:
            if section in base_dict and not base_dict[section]:
                del base_dict[section]
        # move checks to the end of the dict
        if "checks" in base_dict:
            checks = {
                id_: records
                for id_, records in base_dict.pop("checks").items()
                if records
            }
            if checks:
                base_dict["checks"] = checks
        return base_dict

    def __eq__(self, other: "Member"):
        return (
            self.url == other.url
            and self.description == other.description
            and self.license == other.license
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
        if self._filename:
            return self._filename
        flat_name = slugify(
            self.name,
            max_length=11,
            separator="",
            stopwords=["qiskit", "ecosystem"],
            replacements=[["qiskit-addon", ""]],
        )
        return f"{flat_name}_{self.short_uuid}"

    @property
    def badge_md(self):
        """Markdown with the badge for README"""
        return (
            f"[![Qiskit Ecosystem]({self.badge.url})](https://qisk.it/e)"
            if self.badge and self.badge.url
            else None
        )

    def update_github(self):
        """
        Updates all the GitHub information in the project.
        """
        if self.github:
            self.github.update_json()
            self.github.update_owner_repo()

    def update_badge(self):
        """If not there yet, creates a new Bitly link for the badge"""
        if self.badge:
            self.badge.update_url(name=self.name, short_uuid=self.short_uuid)
        else:
            url = BadgeData.create_link(name=self.name, short_uuid=self.short_uuid)
            self.badge = BadgeData(url)

    def update_pypi(self):
        """
        Updates all the PyPI information in the project.
        """
        for package in sorted(self.pypi, key=lambda p: p.package_name):
            package.all_qiskit_versions(force_update=True)
            package.update_json()

    def update_crates(self):
        """
        Updates all the crates.io information in the project.
        """
        for crate in sorted(self.crates, key=lambda c: c.package_name):
            crate.update_json()

    def update_julia(self):
        """
        Updates all the Julia information in the project.
        """
        for package in sorted(self.julia, key=lambda p: p.package_name):
            package.update_json()

    def update_python(self):
        """
        Updates the packaging metadata the project declares in its own repository.

        Unlike the other updaters, this one can *create* its section: the
        distribution name is declared in the repository, so it is discovered here
        rather than submitted. A section that already exists is refreshed, and
        re-keyed if the project renamed its distribution.

        A distribution that is published to PyPI is described by its `[pypi.*]`
        section already, so no section is created for *that* distribution. The
        comparison is by name, not by whether the project publishes anything at
        all: a repository can hold a released distribution and an unreleased one
        next to it, and the second is exactly what this section is for. An
        existing `[python.*]` section is refreshed either way, so a member can be
        given one on purpose to cross-check the source against the release.
        """
        if not self.github or not self.github.owner or not self.github.repo:
            return

        # only what this call discovers is dropped for being published; a section that
        # was declared is kept, because declaring it was deliberate
        discovered = not self.python

        # a member that is one directory of a repository is about what that directory
        # declares: a stored section from anywhere else describes the repository, which is
        # somebody else's business. Two templates of `qiskit-function-templates` each
        # carried the distribution its root publishes, and overwrote each other's page
        subdirectory = self.github.subdirectory
        stored = [
            section
            for section in self.python
            if not subdirectory or (section.path or "").startswith(subdirectory)
        ]
        to_fetch = (
            self.declared_distributions()
            or stored
            or [PythonData.from_github(self.github, path=subdirectory)]
        )
        refreshed = {}
        for python_data in to_fetch:
            python_data.owner = self.github.owner
            python_data.repo = self.github.repo
            python_data.update_json()
            if discovered and python_data.package_name in self.published_distributions:
                continue
            if not python_data.fetched or python_data.package_name is None:
                # The repository declares no distribution any more, so the stored
                # section is stale and dropping it says so. `package_name` alone
                # cannot decide this: it falls back to the stored value, which is
                # what makes a section readable without the network. A repository
                # that could not be read raises instead of getting here, so a
                # failed fetch never drops a good section.
                continue
            # by name and directory: a monorepo can declare the same name twice, and the
            # last fetch of a given one is the one that counts
            refreshed[(python_data.package_name, python_data.path)] = python_data
        self.python = sorted(
            refreshed.values(), key=lambda p: (p.package_name, p.path or "")
        )

    def update_cargo(self):
        """
        Updates the crates the repository declares in a `Cargo.toml`.

        Like `update_python`, this one can *create* its sections: a crate name is declared
        in the repository, so it is discovered here rather than submitted. The manifests
        are the source of truth, so a crate that is gone from them loses its section.

        Three kinds of manifest get no section, for the reasons `ecosystem/cargo.py`
        gives: a crate the project publishes (`[crates.*]` describes it already), a pyo3
        extension module backing the project's Python package, and a workspace root that
        declares no crate of its own.
        """
        if not self.github or not self.github.owner or not self.github.repo:
            return

        sections = {}
        for crate in CargoData.from_github(self.github).candidates():
            crate.update_json()
            if not crate.fetched or not crate.package_name:
                continue
            if crate.package_name in self.published_crates:
                continue
            if crate.is_python_extension:
                continue
            sections[(crate.package_name, crate.path)] = crate
        self.cargo = sorted(
            sections.values(), key=lambda c: (c.package_name, c.path or "")
        )

    def update_requirements(self):
        """
        Updates what the repository's requirements files say about Qiskit.

        Only for a repository that declares no packaging manifest: one that does is
        described by its `[python.*]` or `[pypi.*]` sections, and a requirements file
        next to a manifest is usually a pinned environment rather than a declaration.
        `RequirementsData.candidates` is what applies that rule.

        A file is dropped unless it names qiskit.

        The files a member *declares* are read too, wherever they are: `candidates` looks at
        the root only, and a `docs/requirements.txt` is a judgement rather than a rule, so it
        is declared as a URL in `packages`. A declaration may be a pattern, which is expanded
        against the repository here rather than once at submission time, so a file the project
        adds later is picked up.
        """
        if not self.github or not self.github.owner or not self.github.repo:
            return

        sections = {}
        for requirements in (
            self.declared_requirements()
            + RequirementsData.from_github(self.github).candidates()
        ):
            if requirements.file in sections:
                continue
            requirements.update_json()
            if requirements.fetched and requirements.requires_qiskit:
                sections[requirements.file] = requirements
        self.requirements = list(sections.values()) or None

    def declared_distributions(self):
        """The distributions this member declares, patterns expanded.

        A declaration names the directory a manifest is in, which is the one thing
        discovery cannot find: it reads the repository root only. A pattern
        (`packages/*/pyproject.toml`) is expanded here rather than once at submission time,
        so a directory the project adds later is picked up.

        The stored sections are added too, keyed by the directory they were read from: one
        of them may have been declared before patterns existed, and a section whose
        directory a pattern no longer matches is left to the stale-section rule below.
        """
        declared, paths = [], set()
        for package in self.packages or []:
            if RequirementsData.from_url(package):
                # claimed before `PythonData.from_url` is asked, as `upsert_section_for`
                # does: that one logs an error and raises for a blob URL that is not a
                # manifest, which is the right answer for a submission and noise here
                continue
            try:
                section = PythonData.from_url(package)
            except EcosystemError:
                # a blob URL that is neither a manifest nor a requirements file. The
                # submission path is where that is reported
                continue
            if section is None:
                continue
            for found in section.matches() if section.is_pattern else [section]:
                declared.append(found)
                paths.add(found.path)
        if not declared:
            return []
        declared += [section for section in self.python if section.path not in paths]
        return declared

    def declared_requirements(self):
        """The requirements files this member declares, patterns expanded.

        Only the URLs in `packages` count. The `[[requirements]]` tables are derived from
        them and from the discovery, and reading them back as declarations would keep a
        section the repository no longer justifies: a stored table answers `requires_qiskit`
        from the member file when nothing was fetched, which is what makes a file readable
        offline and exactly what must not decide here.
        """
        declared = []
        for package in self.packages or []:
            section = RequirementsData.from_url(package)
            if section is None:
                continue
            declared += section.matches() if section.is_pattern else [section]
        return declared

    @property
    def published_crates(self):
        """Names of the crates this project publishes to crates.io.

        A `[cargo.*]` section is about a crate nobody can download, so a published one is
        left to `[crates.*]`, as `published_distributions` does for Python.
        """
        return {crate.package_name for crate in self.crates}

    @property
    def published_distributions(self):
        """Canonical names of the Python distributions this project publishes.

        PyPI only. A `[python.*]` section describes something `pip` installs from the
        repository, and a Julia package of the same name is a different artifact in a
        different registry, so it says nothing about whether this distribution is
        released.
        """
        return {canonicalize_name(package.package_name) for package in self.pypi}

    def upsert_sections(self, github_url=None):
        """Create or update sections in a member.
        It is fully local, no validation or internet fetch.
         * github
         * pypi
         * crates
         * julia
         * requirements
         * python
         * badge
        """

        if github_url is None:
            github_url = self.url

        # github section
        if not self.github:
            self.github = GitHubData.from_url(github_url)

        # package sections
        if not self.packages:
            self.packages = []

        for package in self.packages:
            self.upsert_section_for(package)

        # badge section. Only the style, so it can be reviewed (and changed) in the submission
        # PR. The url needs Bitly and is created when the submission is accepted, see
        # .github/workflows/welcome-new-member.yml
        if not self.badge:
            self.badge = BadgeData()

    def upsert_section_for(self, package):
        """Puts a declared URL under the section it belongs to, and says which one that is.

        The order is what resolves a URL that more than one section could read:
        `RequirementsData.from_url` claims a requirements file before `PythonData.from_url`
        sees it, because that one *raises* for a blob URL that is not a manifest, which is
        what tells a submitter they linked the wrong file.

        Returns the name of the section, or None for a URL no section reads: a registry with
        no section of its own, which is what the project page lists as "other registries".
        """
        if pypi := PyPIData.from_url(package):
            self.pypi = self._with(self.pypi, pypi)
            return "pypi"
        if crates := CratesData.from_url(package):
            self.crates = self._with(self.crates, crates)
            return "crates"
        if julia := JuliaData.from_url(package):
            self.julia = self._with(self.julia, julia)
            return "julia"
        if RequirementsData.from_url(package):
            return "requirements"
        if PythonData.from_url(package):
            return "python"
        return None

    @staticmethod
    def _with(sections, section):
        """`sections` plus `section`, unless something of that name is already there.

        A declaration read twice is one entry, which is what the key used to guarantee. The
        stored one wins: it carries whatever the last fetch read, and this one is unfetched.
        """
        if any(stored.package_name == section.package_name for stored in sections):
            return sections
        return sorted(sections + [section], key=lambda s: s.package_name)

    def declares_a_section(self, package):
        """Whether a declared URL is read by a section of this member.

        The project page asks this to leave the URLs it already describes out of the list of
        other registries. It builds nothing: `upsert_section_for` is what does that.
        """
        if PyPIData.from_url(package) or JuliaData.from_url(package):
            return True
        if CratesData.from_url(package):
            return True
        if RequirementsData.from_url(package):
            return True
        try:
            return bool(PythonData.from_url(package))
        except EcosystemError:
            # a blob URL that is not a manifest and not a requirements file: not a registry
            # either, so the page has nothing to say about it
            return True

    @classmethod
    def from_submission(cls, submission, issue_number: str = None):
        """
        Takes a submission object and creates a very basic Member object
        """
        skip_checks = {}
        if submission.skip:
            xfailed_until = date.today() + relativedelta(
                months=cls.DEFAULT_XFAILED_PERIOD_IN_MONTHS
            )
            for check_id, reason in submission.skip:
                skip_checks[check_id] = [
                    CheckData(check_id, xfailed=reason, xfailed_until=xfailed_until)
                ]
        return Member(
            name=submission.name,
            submission_number=issue_number,
            url=submission.source_url,
            description=submission.description,
            contact_info=submission.contact_info,
            labels=submission.labels,
            interfaces=submission.interfaces,
            ibm_maintained=submission.is_ibm_maintained,
            website=submission.home_url,
            category=submission.category,
            reference_paper=submission.paper_url,
            documentation=submission.docs_url,
            maturity=submission.maturity,
            packages=submission.package_urls,
            checks=skip_checks or None,
        )

    @property
    def failing_checkups(self):
        """The check ups of this member that nothing explains away.

        The counterpart of `xfails`: between the two, every recorded check up is counted
        once, which is the split the check up page makes (`docs/checkup_page.py`).
        """
        return [
            check
            for records in self.checks.values()
            for check in records
            if not check.xfail_applies
        ]

    @property
    def xfails(self):
        """list of xfails for a self member.

        A check up whose `xfailed_until` has passed is not in the list: the explanation is no
        longer valid, so the check up is verified again as a regular one."""
        return [
            check
            for records in self.checks.values()
            for check in records
            if check.xfail_applies
        ]

    def stored_record(self, checkup_id, subtest=None):
        """The stored record a new result for one place continues, if there is one.

        By place first, so each place keeps its own `since` and its own explanation. A stored
        record that names no place is the fallback: that is what a record written before the
        places were recorded looks like, and what a check up with one answer per member
        always looks like.
        """
        records = self.checks.get(checkup_id, [])
        for record in records:
            if record.subtest == subtest:
                return record
        for record in records:
            if record.subtest is None:
                return record
        return None

    def explanation_for(self, checkup_id, subtest=None):
        """The live explanation this member has for one place of a check up, if any.

        A stored record that names no place answers for every place: that is what a record
        written before the places were recorded looks like, and what a check up with one
        answer per member always looks like.
        """
        live = [
            record for record in self.checks.get(checkup_id, []) if record.xfail_applies
        ]
        for record in live:
            if record.subtest == subtest:
                return record.xfailed
        for record in live:
            if record.subtest is None:
                return record.xfailed
        return None

    def update_checkups(self, checker=None):
        """Runs validation tests and updates the check-ups sections"""
        checkups = {}
        if checker is None:
            report = validate_member(self, verbose_level="-q")
        else:
            report = validate_member(self, verbose_level="-v", tests_to_run=checker)

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
            stored = self.stored_record(checkup_data.id, checkup_data.subtest)
            if stored:
                # Fields to preserve, from the record about the same place
                checkup_data.discussion = stored.discussion
                # the clock of this place, which is why it did not restart
                checkup_data.since = stored.since or checkup_data.since
                if checkup_data.xfailed:
                    # the report only carries the explanation, not its expiration date
                    checkup_data.xfailed_until = stored.xfailed_until
            if not checkup_data.since and not checkup_data.xfailed:
                # a place failing for the first time starts its cure period today. The
                # report of a place cannot say so itself: the `previously_failed` marker it
                # would read is about the check up, not about one of its places
                checkup_data.since = CheckData.today
            checkups.setdefault(checkup_data.id, []).append(checkup_data)

        for checkup_id, records in self.checks.items():
            source_based = [record for record in records if record.source]
            if not source_based:
                continue
            for checkup in source_based:
                # A source-based check up does not come from a test, so it is not in the
                # report. It stands as long as its source issue does, and it takes precedence
                # over the result of the checker with the same ID.
                if checkup.xfailed and checkup.xfailed_expired:
                    # Not being in the report also means that the loop above does not drop an
                    # expired explanation, so it is dropped here. From now on, the check up
                    # counts as a regular failure.
                    checkup.xfailed = None
                    checkup.xfailed_until = None
                    checkup.since = checkup.since or CheckData.today
                checkup.update_from_source()
            checkups[checkup_id] = source_based

        self.checks = checkups

    @property
    def age_in_months(self):
        """Months since the GitHub repository was created.
        None if there is no member.github.created_at"""
        created_at = parse_date(getattr(self.github, "created_at", None))
        if created_at is None:
            return None
        relative = relativedelta(date.today(), created_at)
        return (relative.years * 12) + relative.months

    @property
    def is_alumni(self):
        """True if the project has been retired from the ecosystem.

        Unlike `unmaintained`, this *is* the status: `Alumni` is terminal, so nothing
        masks it. It answers "is this still a member?", which is why the check ups do
        not apply to it and why it is kept out of the listings on the summary page,
        while its own pages stay published so existing links keep resolving.
        """
        return self.status == "Alumni"

    @property
    def unmaintained(self):
        """True if the project declares no maintenance expectations.

        This is what the `Unmaintained` status is derived from, but it is not the same thing:
        `self.status` is masked by `Under revision` as soon as any check up is pending, so a
        check up asking "is this project maintained?" has to use this instead of the status.
        """
        return self.maturity in ["as-is", "deprecated"]

    @property
    def early(self):
        """True if the GitHub repository is younger than 12 months."""
        if self.age_in_months is None:
            return False
        return self.age_in_months < 12

    @property
    def very_early(self):
        """True if the GitHub repository is younger than 3 months"""
        if self.age_in_months is None:
            return False
        return self.age_in_months < 3
