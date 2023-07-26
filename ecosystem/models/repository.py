"""Repository model."""
import pprint
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass

from . import RepositoryConfiguration
from .test_results import TestResult, StyleResult, CoverageResult
from .tier import Tier
from .utils import JsonSerializable, new_list


@dataclass
class Repository(JsonSerializable):
    """Main repository class."""

    # pylint: disable=too-many-instance-attributes
    name: str
    url: str
    description: str
    licence: str
    contact_info: Optional[str] = None
    alternatives: Optional[str] = None
    affiliations: Optional[str] = None
    labels: List[str] = new_list()
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    tier: str = Tier.COMMUNITY
    website: Optional[str] = None
    tests_results: List[TestResult] = new_list()
    styles_results: List[TestResult] = new_list()
    coverages_results: List[TestResult] = new_list()
    configuration: Optional[RepositoryConfiguration] = None
    skip_tests: Optional[bool] = False
    historical_test_results: List[TestResult] = new_list()
    stars: Optional[int] = None

    def __post_init__(self):
        self.__dict__.setdefault("created_at", datetime.now().timestamp())
        self.__dict__.setdefault("updated_at", datetime.now().timestamp())

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Transform dictionary to Repository.

        Args:
            dictionary: dict object

        Return: Repository
        """
        for key, dtype in [
            ("tests_results", TestResult),
            ("styles_results", StyleResult),
            ("coverages_results", CoverageResult),
            ("historical_test_results", TestResult),
        ]:
            dictionary[key] = [dtype.from_dict(r) for r in dictionary.get(key, [])]

        if "configuration" in dictionary:
            dictionary["configuration"] = RepositoryConfiguration.from_dict(
                dictionary.get("configuration")
            )

        return Repository(**dictionary)

    def __eq__(self, other: "Repository"):
        return (
            self.tier == other.tier
            and self.url == other.url
            and self.description == other.description
            and self.licence == other.licence
        )

    def __repr__(self):
        return pprint.pformat(self.to_dict(), indent=4)

    def __str__(self):
        return f"Repository({self.tier} | {self.name} | {self.url})"
