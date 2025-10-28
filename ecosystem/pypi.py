"""PyPI section."""

from functools import reduce
from urllib.parse import ParseResult
from re import match
from os import path
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
import json
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from datetime import datetime

from jsonpath import findall

from .serializable import JsonSerializable
from .error_handling import EcosystemError, logger
from .request import request_json


class PyPIData(JsonSerializable):
    """
    The PyPI data related to a project
    """

    dict_keys = ["package_name", "version", "requires_qiskit", 'compatible_with_qiskit_v1', 'compatible_with_qiskit_v2', 'release_date_of_the_last_qiskit_version_supported', 'last_qiskit_version_supported']
    aliases = {"version": "info.version"}
    json_types = {}
    reduce = {}

    def __init__(self, package_name: str, **kwargs):
        self.package_name = canonicalize_name(package_name, validate=True)
        self._kwargs = kwargs or {}
        self._pypi_json = None
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
        if "pypi.org" not in pypi_project_url:
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

    def compatible_with_qiskit(self, major):
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

    def all_qiskit_versions(self, force_update=False):

        dir_path = path.dirname(path.realpath(__file__))
        all_qiskit_versions_json = path.join(dir_path, 'all_qiskit_versions.json')
        if force_update:
            qiskit_json = request_json(f"pypi.org/pypi/qiskit/json")
            str_versions = findall('$.releases.~', qiskit_json)
            self._all_qiskit_versions = {}
            for str_version in str_versions:
                str_dates = findall(f'$.releases["{str_version}"].*.upload_time_iso_8601', qiskit_json)
                if not str_dates:
                    raise EcosystemError("Qiskit {str_version} has no release?")
                last_date = max(datetime.fromisoformat(d) for d in str_dates)
                self._all_qiskit_versions[str_version] = {'upload_at': last_date}
            with open(all_qiskit_versions_json, 'w') as json_file:
                json.dump(self._all_qiskit_versions, json_file, indent=4, default=str)

        if self._all_qiskit_versions is None:
            try:
                with open(all_qiskit_versions_json) as data_file:
                    versions_dates_dict = json.load(data_file)
            except FileNotFoundError:
                logger.warning(f'{all_qiskit_versions_json} not found. Getting it back fom PyPI')
                return self.all_qiskit_versions(force_update=True)
            self._all_qiskit_versions = {k: {'upload_at': datetime.fromisoformat(v['upload_at'])}
                                         for k,v in versions_dates_dict.items()}
        return self._all_qiskit_versions

    @property
    def compatible_with_qiskit_v1(self):
        return self.compatible_with_qiskit(major=1)

    @property
    def compatible_with_qiskit_v2(self):
        return self.compatible_with_qiskit(major=2)

    @property
    def last_qiskit_version_supported(self):
        if self.requires_qiskit is None:
            return None
        return self.last_qiskit_version_supported_with_date()[0]

    @property
    def release_date_of_the_last_qiskit_version_supported(self):
        if self.requires_qiskit is None:
            return None
        return self.last_qiskit_version_supported_with_date()[1]

    def last_qiskit_version_supported_with_date(self):
        if self.requires_qiskit is None:
            return None
        qiskit_specifier = SpecifierSet(self.requires_qiskit)
        all_qiskit_versions = sorted(self.all_qiskit_versions().items(), key=lambda x: x[1]['upload_at'], reverse=True)
        for qiskit_version, version_data in all_qiskit_versions:
            if qiskit_specifier.contains(qiskit_version):
                return qiskit_version, version_data['upload_at']
