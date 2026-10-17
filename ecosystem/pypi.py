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

"""PyPI section."""

from functools import reduce
from re import match, sub

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

from jsonpath import findall

from .license import License
from .serializable import JsonSerializable, parse_date
from .error_handling import EcosystemError, logger
from .qiskit_requirement import QiskitRequirementMixin
from .request import request_json


class QiskitRequirement(QiskitRequirementMixin, JsonSerializable):
    """One qiskit requirement a release declares, and the condition it is under.

    A release can ask for qiskit several times: behind an extra (`pip install
    pkg[qiskit]`), under an environment marker, or through another dependency. Each of
    those is its own requirement with its own resolved compatibility, which is why the
    four derived fields live here rather than on the distribution: a specifier that only
    applies on Python 3.14 resolves differently from the one that applies below it.

    The shape `[[requirements]]` has, for the same reason: a specifier plus what the
    mixin derives from it, with no name of its own to be keyed by.
    """

    dict_keys = [
        "specifier",
        "extra",
        "environment",
        "via",
        "compatible_with_qiskit_v1",
        "compatible_with_qiskit_v2",
        "highest_supported_qiskit_release_date",
        "highest_supported_qiskit_version",
    ]

    def __init__(
        self,
        specifier: str = None,
        extra: str = None,
        environment: str = None,
        via: str = None,
        **kwargs,
    ):
        """
        Args:
            specifier: the PEP 440 specifier, `>=0` for a bare `qiskit`.
            extra: the extra that has to be requested for this to apply. None means a
                plain install gets it.
            environment: the rest of the PEP 508 marker, once the `extra ==` part is
                taken out. None means it always applies.
            via: the dependency this is reached through, as the release declares it.
                None means the release requires qiskit itself.
        """
        self.specifier = specifier
        self.extra = extra
        self.environment = environment
        self.via = via
        self._kwargs = kwargs or {}
        self._all_qiskit_versions = None

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self, keys=None) -> dict:
        return super().to_dict(keys=keys or QiskitRequirement.dict_keys)

    @property
    def requires_qiskit(self):
        """What the mixin resolves, which here is the specifier itself"""
        return self.specifier

    @property
    def fetched(self):
        """Always true: the specifier is the requirement, so there is nothing to fetch.

        What the mixin asks with this is whether a stored value is all it has to go on,
        and here it never is.
        """
        return True

    @property
    def declared_by(self):
        """What the warnings name"""
        return f"qiskit{self.specifier}" + (
            f" (extra {self.extra})" if self.extra else ""
        )

    @property
    def conditional(self):
        """True when something has to be true beyond installing the release.

        An extra has to be requested, an environment has to match, or another dependency
        is what brings qiskit in. A requirement with none of those is what a plain
        `pip install` creates.
        """
        return bool(self.extra or self.environment or self.via)


class PyPIData(
    QiskitRequirementMixin, JsonSerializable
):  # pylint: disable=too-many-public-methods
    """
    The PyPI data related to a project
    """

    dict_keys = [
        "package_name",
        "version",
        "last_release_date",
        "license",
        "description",
        "url",
        "development_status",
        "status",
        "maintainers",
        "requires_qiskit",
        "requires",
        "compatible_with_qiskit_v1",
        "compatible_with_qiskit_v2",
        "highest_supported_qiskit_release_date",
        "highest_supported_qiskit_version",
        "last_month_downloads",
        "last_180_days_downloads",
    ]
    aliases = {
        "version": "info.version",
        "url": "info.package_url",
        "description": "info.summary",
        "development_status": "info.classifiers[?('Development Status' in @)]",
    }
    # runs on each findall element
    json_types = {
        "info.classifiers[?('Development Status' in @)]": lambda x: x.split(" :: ")[-1]
    }
    reduce = {}  # if findall returns more than one element

    def __init__(self, package_name: str, **kwargs):
        self.package_name = canonicalize_name(package_name, validate=True)
        self._kwargs = kwargs or {}
        self._pypi_json = None
        self._pypi_simple_json = None
        self._pypistats_json = None
        self._all_qiskit_versions = None

    def __repr__(self):
        return str(self.to_dict())

    @classmethod
    def from_dict(cls, dictionary: dict):
        if dictionary.get("requires"):
            dictionary["requires"] = [
                QiskitRequirement(**row) for row in dictionary["requires"]
            ]
        if "license" in dictionary and dictionary["license"] is not None:
            dictionary["license"] = License(dictionary["license"], where="pypi")
        return super().from_dict(dictionary)

    @classmethod
    def from_url(cls, pypi_project_url):
        """
        Builds a PyPISection from an URL that looks like
        'https://pypi.org/project/<package_name>/'.
        Returns None if the given URL is not a PyPI url
        """
        if "pypi.org" not in pypi_project_url.hostname:
            # pypi_project_url is not a PyPI URL
            return None

        url_path = pypi_project_url.path

        path_parts = [c for c in url_path.split("/") if match(r"^[A-Za-z0-9_.-]+$", c)]
        if len(path_parts) == 2 and path_parts[0].lower() == "project":
            return PyPIData(package_name=path_parts[1].lower())

        raise EcosystemError(f"invalid PyPI url: {pypi_project_url}")

    def update_json(self):
        """
        Fetches remote jsons data from:
          - https://pypi.org/pypi/{self.package_name}/json
          - https://pypi.org/simple/{self.package_name}/
          - https://pypistats.org/api/packages/{self.package_name}/
        """
        self._pypi_json = self.request_pypi()
        self._pypi_simple_json = self.request_pypi_simple()
        if self._pypistats_json is None:
            self._pypistats_json = self.request_pypistats()

    def request_pypi(self):
        """Fetches https://pypi.org/pypi/{self.package_name}/json"""
        try:
            return request_json(f"pypi.org/pypi/{self.package_name}/json")
        except EcosystemError:
            return None

    def request_pypi_simple(self):
        """Fetches https://pypi.org/simple/{self.package_name}/"""
        try:
            return request_json(
                f"https://pypi.org/simple/{self.package_name}/",
                headers={"Accept": "application/vnd.pypi.simple.v1+json"},
            )
        except EcosystemError:
            return None

    def __getattr__(self, item):
        if self._pypi_json:
            if item in PyPIData.aliases:
                item = PyPIData.aliases[item]

            json_elements = findall(item, self._pypi_json)
            if item in PyPIData.json_types:
                json_elements = [PyPIData.json_types[item](e) for e in json_elements]

            if len(json_elements) == 1:
                return json_elements[0]

            if len(json_elements) >= 2:
                return reduce(PyPIData.reduce[item], json_elements)

            raise AttributeError(
                f"'{type(self).__name__}' object has no " f"attribute '{item}'"
            )

        if item in self._kwargs:
            return self._kwargs[item]

        if item in self.dict_keys:
            return None

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{item}'"
        )

    @property
    def last_release_date(self):
        """Date of the last release in PyPI"""
        last_release = self.pypi_json.get("releases", {}).get(self.version, None)
        return (
            max(parse_date(r["upload_time"]) for r in last_release)
            if last_release
            else self._kwargs.get("last_release_date")
        )

    @property
    def pypi_json(self):
        """if the JSON was not fetch from PyPI, return empty dict"""
        return self._pypi_json or {}

    @property
    def fetched(self):
        """True once `update_json` has read the PyPI JSON.

        `requires_qiskit` is overridden here and reads `pypi_json` directly, so this is
        only what the mixin asks: whether a stored value is all this section has.
        """
        return self._pypi_json is not None

    @property
    def requires(self):
        """Every qiskit requirement the release declares, and the condition each is under.

        A release can ask for qiskit more than once: behind an extra (`pip install
        pkg[qiskit]`), under an environment marker (`python_version >= "3.14"`), or both,
        and `requires_qiskit` above is only the effective one. The distribution stays a
        single section, so its release and download fields are stated once; what varies is
        the condition, not the distribution.

        `via` is not derived here. It names the dependency a requirement is reached
        through, which is a statement about another project's metadata rather than this
        one's, so it is written by hand until something resolves the chain.
        """
        conditions, seen = [], set()
        for requirement in self._qiskit_requirements():
            marker = str(requirement.marker or "")
            found = {"specifier": str(requirement.specifier) or ">=0"}
            extra = match(r'.*extra == "([^"]+)"', marker)
            if extra:
                found["extra"] = extra.group(1)
                # what is left once the extra is taken out, which is the environment
                marker = sub(
                    r'\s*and\s*extra == "[^"]+"|extra == "[^"]+"\s*and\s*|extra == "[^"]+"',
                    "",
                    marker,
                ).strip()
            if marker:
                found["environment"] = marker
            key = tuple(sorted(found.items()))
            if key not in seen:
                seen.add(key)
                conditions.append(QiskitRequirement(**found))
        stored = [
            row if isinstance(row, QiskitRequirement) else QiskitRequirement(**row)
            for row in self._kwargs.get("requires") or []
        ]
        if conditions:
            # a `via` written by hand survives a refresh: it says what this release is
            # reached through, which the release's own metadata cannot contradict
            return conditions + [row for row in stored if row.via]
        return stored or None

    def _qiskit_requirements(self):
        """The parsed `requires_dist` entries that name qiskit, in the order PyPI lists them"""
        for requirement_str in (
            self.pypi_json.get("info", {}).get("requires_dist") or []
        ):
            try:
                requirement = Requirement(requirement_str)
            except InvalidRequirement:
                logger.warning(
                    "%s declares an unparseable requirement: %r",
                    self.package_name,
                    requirement_str,
                )
                continue
            if canonicalize_name(requirement.name) == "qiskit":
                yield requirement

    def to_dict(self, keys=None) -> dict:
        """The section as a member file stores it.

        The qiskit fields are dropped when every requirement is conditional: a release
        whose qiskit lives behind an extra does not require qiskit, and saying so at this
        level asserts a dependency a plain `pip install` does not create. The entries in
        `requires` carry the specifier and what it resolves to, each under its own
        condition.
        """
        section = super().to_dict(keys=keys or PyPIData.dict_keys)
        requires = self.requires
        if requires and all(row.conditional for row in requires):
            for field in (
                "requires_qiskit",
                "compatible_with_qiskit_v1",
                "compatible_with_qiskit_v2",
                "highest_supported_qiskit_release_date",
                "highest_supported_qiskit_version",
            ):
                section.pop(field, None)
        return section

    @property
    def requires_qiskit(self):
        """String with the specifier for "qiskit" dependency"""
        requires_dist = self.pypi_json.get("info", {}).get("requires_dist") or []
        for requirement_str in requires_dist:
            requirement = Requirement(requirement_str)
            if requirement.name == "qiskit":
                if len(requirement.specifier):
                    self._kwargs["requires_qiskit"] = str(requirement.specifier)
                elif (
                    "requires_qiskit" not in self._kwargs
                    or self._kwargs["requires_qiskit"] != ">=0"
                ):
                    logger.warning(
                        "%s depends on qiskit but with empty specifier. "
                        'Forcing one, ">=0"',
                        self.package_name,
                    )
                    self._kwargs["requires_qiskit"] = ">=0"
                return self._kwargs["requires_qiskit"]
        if "requires_qiskit" in self._kwargs:
            return self._kwargs["requires_qiskit"]
        return None

    def request_pypistats(self):
        """uses pypistats to get stats about python package"""
        getters = ["recent", "overall"]
        ret = {}
        for getter in getters:
            try:
                raw_data = request_json(
                    f"https://pypistats.org/api/packages/{self.package_name}/{getter}",
                    delay=3,
                )
            except EcosystemError as err:
                if "Not Found (404)" in err.message:
                    return ret
                raise err

            if isinstance(raw_data["data"], list):
                ret[raw_data["type"]] = {
                    "with_mirrors": sum(
                        i["downloads"]
                        for i in raw_data["data"]
                        if i["category"] == "with_mirrors"
                    ),
                    "without_mirrors": sum(
                        i["downloads"]
                        for i in raw_data["data"]
                        if i["category"] == "without_mirrors"
                    ),
                }
            else:
                ret[raw_data["type"]] = raw_data["data"]
        return ret

    @property
    def last_month_downloads(self):
        """Last month downloads say something about current popularity"""
        if self._pypistats_json:
            return self._pypistats_json.get("recent_downloads", {}).get("last_month")
        return self._kwargs.get("last_month_downloads")

    @property
    def last_180_days_downloads(self):
        """Last 180-day downloads say something about current popularity"""
        if self._pypistats_json:
            return self._pypistats_json.get("overall_downloads", {}).get(
                "without_mirrors"
            )
        return self._kwargs.get("last_180_days_downloads")

    @property
    def license(self):
        """Package license: what PyPI says, or the stored value when nothing was fetched"""
        from_pypi = self._license_from_pypi() if self._pypi_json else None
        if from_pypi:
            return from_pypi
        stored = self._kwargs.get("license")
        if stored is None:
            return None
        return stored if isinstance(stored, License) else License(stored, "pypi")

    def _license_from_pypi(self):
        """The license the fetched JSON states, from its most explicit field down.

        A `License:` field short enough to be a name, then a license expression, and last the trove
        classifier.
        """
        info = self._pypi_json.get("info", {})
        text = info.get("license")
        if text and len(text) < 50:
            return License(text, "pypi")
        expression = info.get("license_expression")
        if expression:
            return License(expression, "pypi")

        for classifier in info.get("classifiers") or []:
            parts = [part.strip() for part in classifier.split("::")]
            if classifier.startswith("License :: ") and len(parts) == 3:
                return License(parts[2], "pypi")
        return None

    @property
    def maintainers(self):
        """Package maintainers (or owners)"""
        maintainers = []
        if self._pypi_json:
            ownership = self._pypi_json.get("ownership")
            organization = ownership.get("organization")
            if organization:
                maintainers.append(f"https://pypi.org/org/{organization}/")
            maintainers += [
                f"https://pypi.org/user/{u['user']}/"
                for u in ownership["roles"]
                if u["role"] == "Owner"
            ]
        return maintainers or self._kwargs.get("maintainers")

    @property
    def status(self):
        """Project status"""
        project_status = None
        if self._pypi_simple_json:
            return self._pypi_simple_json.get("project-status", {}).get("status")
        return project_status or self._kwargs.get("status")
