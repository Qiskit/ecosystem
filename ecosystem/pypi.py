"""PyPI section."""

from functools import reduce, cached_property
from urllib.parse import ParseResult
from re import match
from os import path
import json

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.specifiers import SpecifierSet
from packaging.version import Version
import pypistats

from jsonpath import findall


from .serializable import JsonSerializable, parse_datetime
from .error_handling import EcosystemError, logger
from .request import request_json


class PyPIData(JsonSerializable):
    """
    The PyPI data related to a project
    """

    dict_keys = [
        "package_name",
        "version",
        "url",
        "requires_qiskit",
        "compatible_with_qiskit_v1",
        "compatible_with_qiskit_v2",
        "highest_supported_qiskit_release_date",
        "highest_supported_qiskit_version",
        "last_month_downloads",
        "last_180_days_downloads",
    ]
    aliases = {"version": "info.version", "url": "info.package_url"}
    json_types = {}
    reduce = {}

    def __init__(self, package_name: str, **kwargs):
        self.package_name = canonicalize_name(package_name, validate=True)
        self._kwargs = kwargs or {}
        self._pypi_json = None
        self._pypistats_json = None
        self._all_qiskit_versions = None

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self) -> dict:
        dictionary = {}
        for key in PyPIData.dict_keys:
            value = getattr(self, key, None)
            if value is not None:
                dictionary[key] = value
        return dictionary

    @classmethod
    def from_url(cls, pypi_project_url: ParseResult):
        """
        Builds a PyPISection from an URL (ParseResult) that looks like
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
        Fetches remote json data from https://pypi.org/pypi/{self.package_name}/json
        """
        try:
            self._pypi_json = request_json(f"pypi.org/pypi/{self.package_name}/json")
        except EcosystemError:
            pass
        self._pypistats_json = self.request_pypistats()

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

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{item}'"
        )

    @property
    def pypi_json(self):
        """if the JSON was not fetch from PyPI, return empty dict"""
        return self._pypi_json or {}

    @property
    def requires_qiskit(self):
        """String with the specifier for "qiskit" dependency"""
        if "requires_qiskit" in self._kwargs:
            return self._kwargs["requires_qiskit"]
        requires_dist = self.pypi_json.get("info", {}).get("requires_dist") or []
        for requirement_str in requires_dist:
            requirement = Requirement(requirement_str)
            if requirement.name == "qiskit":
                self._kwargs["requires_qiskit"] = str(requirement.specifier)
                if self._kwargs["requires_qiskit"] == "":
                    logger.warning(
                        "%s depends on qiskit but with empty specifier. "
                        'Forcing one, ">=0"',
                        self.package_name,
                    )
                    self._kwargs["requires_qiskit"] = ">=0"
                return self._kwargs["requires_qiskit"]
        return None

    def all_qiskit_versions(self, force_update=False):
        """Returns a dictionary with all the Qiskit releases,
        with version numbers as key and extra data"""
        dir_path = path.dirname(path.realpath(__file__))
        all_qiskit_versions_json = path.join(dir_path, "all_qiskit_versions.json")
        if force_update:
            qiskit_json = request_json("pypi.org/pypi/qiskit/json")
            str_versions = findall("$.releases.~", qiskit_json)
            self._all_qiskit_versions = {}
            for str_version in str_versions:
                str_dates = findall(
                    f'$.releases["{str_version}"].*.upload_time_iso_8601', qiskit_json
                )
                if not str_dates:
                    raise EcosystemError("Qiskit {str_version} has no release?")
                last_date = max(parse_datetime(d) for d in str_dates)
                self._all_qiskit_versions[str_version] = {"upload_at": last_date}
            with open(all_qiskit_versions_json, "w") as json_file:
                json.dump(self._all_qiskit_versions, json_file, indent=4, default=str)

        if self._all_qiskit_versions is None:
            try:
                with open(all_qiskit_versions_json) as data_file:
                    versions_dates_dict = json.load(data_file)
            except FileNotFoundError:
                logger.warning(
                    "%s not found. Getting it back fom PyPI", all_qiskit_versions_json
                )
                return self.all_qiskit_versions(force_update=True)
            self._all_qiskit_versions = {
                k: {"upload_at": parse_datetime(v["upload_at"])}
                for k, v in versions_dates_dict.items()
            }
        return self._all_qiskit_versions

    def compatible_with_qiskit(self, major):
        """Boolean if the package is compatible with any Qiskit of the v<major> series"""
        if self.requires_qiskit is None:
            return None
        qiskit_specifier = SpecifierSet(self.requires_qiskit)
        qiskit_versions = self.all_qiskit_versions()
        for qiskit_version in qiskit_versions.keys():
            if Version(qiskit_version).major != major:
                continue
            if qiskit_specifier.contains(qiskit_version):
                break
        else:
            return False
        return True

    @property
    def compatible_with_qiskit_v1(self):
        """Boolean if the package is compatible with any Qiskit of the v1 series"""
        return self.compatible_with_qiskit(major=1)

    @property
    def compatible_with_qiskit_v2(self):
        """Boolean if the package is compatible with any Qiskit of the v2 series"""
        return self.compatible_with_qiskit(major=2)

    @property
    def highest_supported_qiskit_version(self):
        """Returns the highest supported Qiskit version"""
        if self.requires_qiskit is None:
            return None
        return self.highest_supported_qiskit_version_and_release_date[0]

    @property
    def highest_supported_qiskit_release_date(self):
        """Returns when was released the highest supported Qiskit version"""
        if self.requires_qiskit is None:
            return None
        return self.highest_supported_qiskit_version_and_release_date[1]

    @cached_property
    def highest_supported_qiskit_version_and_release_date(self):
        """Returns the highest supported Qiskit version and when it was released"""
        if self.requires_qiskit is None:
            return None
        qiskit_specifier = SpecifierSet(self.requires_qiskit)
        all_qiskit_versions = sorted(
            self.all_qiskit_versions().items(),
            key=lambda x: Version(x[0]),
            reverse=True,
        )
        for qiskit_version, version_data in all_qiskit_versions:
            if qiskit_specifier.contains(qiskit_version):
                return qiskit_version, version_data["upload_at"]
        return None

    def request_pypistats(self):
        """uses pypistats to get stats about python package"""
        getters = ["recent", "overall", "python_minor", "system"]
        ret = {}
        for getter in getters:
            raw_data = json.loads(
                getattr(pypistats, getter)(self.package_name, format="json")
            )
            if isinstance(raw_data["data"], list):
                ret[raw_data["type"]] = {
                    i["category"]: i["downloads"] for i in raw_data["data"]
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
