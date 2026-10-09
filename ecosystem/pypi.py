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
from re import match

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from jsonpath import findall

from .license import License
from .serializable import JsonSerializable, parse_date
from .error_handling import EcosystemError, logger
from .qiskit_requirement import QiskitRequirementMixin
from .request import request_json


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

    def to_dict(self, keys=None) -> dict:
        return super().to_dict(keys=keys or PyPIData.dict_keys)

    @classmethod
    def from_dict(cls, dictionary: dict):
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
