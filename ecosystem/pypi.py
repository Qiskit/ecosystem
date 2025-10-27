"""PyPI section."""

from functools import reduce
from urllib.parse import ParseResult
from re import match
from collections import namedtuple
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from jsonpath import findall

from .serializable import JsonSerializable, Alias
from .error_handling import EcosystemError, logger
from .request import request_json



class PyPIData(JsonSerializable):
    """
    The PyPI data related to a project
    """

    aliases = {"version": Alias("info.version", sum)}
    dict_keys = ["project", "version", "requires_qiskit"]

    def __init__(self, project: str, **kwargs):
        self.project = canonicalize_name(project, validate=True)
        self._kwargs = kwargs or {}
        self._pypi_json = None

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
        Builds a PyPISection from an url. Returns None
        if the given url is not a PyPI url
        """
        if "pypi.org" not in pypi_project_url:
            # pypi_project_url is not a PyPI URL
            return None

        url_path = pypi_project_url.path

        path_parts = [c for c in url_path.split("/") if match(r"^[A-Za-z0-9_.-]+$", c)]
        if len(path_parts) == 2 and path_parts[0].lower() == "project":
            return PyPIData(project=path_parts[1].lower())

        raise EcosystemError(f"invalid PyPI url: {pypi_project_url}")

    def update_json(self):
        """
        Fetches remote json data from https://pypi.org/pypi/{self.project}/json
        """
        try:
            self._pypi_json = request_json(f"pypi.org/pypi/{self.project}/json")
        except EcosystemError:
            pass

    def __getattr__(self, item):
        reduce_func = None

        if self._pypi_json:
            if item in PyPIData.pypi_aliases:
                item, reduce_func = PyPIData.pypi_aliases[item]
            json_elements = findall(item, self._pypi_json)
            if len(json_elements) == 0:
                raise AttributeError(
                    f"'{type(self).__name__}' object has no attribute '{item}'"
                )
            if reduce_func:
                return reduce(reduce_func, json_elements)
            return json_elements[0]

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
                        self.project,
                    )
                    self._kwargs["requires_qiskit"] = ">=0"
                return self._kwargs["requires_qiskit"]
        return None
