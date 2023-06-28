"""Repository model."""
import pprint
from datetime import datetime
from typing import Optional, List

from . import RepositoryConfiguration
from .test_results import TestResult, StyleResult, CoverageResult
from .tier import Tier
from .utils import JsonSerializable


class Repository(JsonSerializable):
    """Main repository class."""

    # pylint: disable=too-many-locals, too-many-instance-attributes

    def __init__(
        self,
        name: str,
        url: str,
        description: str,
        licence: str,
        contact_info: Optional[str] = None,
        alternatives: Optional[str] = None,
        affiliations: Optional[str] = None,
        labels: Optional[List[str]] = None,
        website: Optional[List[str]] = None,
        created_at: Optional[int] = None,
        updated_at: Optional[int] = None,
        tier: str = Tier.COMMUNITY,
        tests_results: Optional[List[TestResult]] = None,
        styles_results: Optional[List[TestResult]] = None,
        coverages_results: Optional[List[TestResult]] = None,
        configuration: Optional[RepositoryConfiguration] = None,
        skip_tests: Optional[bool] = None,
        historical_test_results: Optional[List[TestResult]] = None,
        stars: Optional[int] = None,
    ):
        """Repository class.

        Args:
            name: name of project
            url: url to github repo
            description: description
            licence: licence
            contact_info: contact information
            alternatives: alternatives to project
            affiliations : affiliations of the project
            website : website for the project
            labels: labels
            created_at: creation date
            updated_at: update date
            tests_results: tests passed by repo
            styles_results: styles passed by repo
            coverages_results: coverages passed by repo
            skip_tests: weather skip tests or not
            historical_test_results: list of historical test results
            stars: github stars for repo
        """
        self.name = name
        self.url = url
        self.description = description
        self.licence = licence
        self.contact_info = contact_info
        self.alternatives = alternatives
        self.affiliations = affiliations
        self.website = website
        self.labels = labels if labels is not None else []
        self.created_at = (
            created_at if created_at is not None else datetime.now().timestamp()
        )
        self.updated_at = (
            updated_at if updated_at is not None else datetime.now().timestamp()
        )
        self.tests_results = tests_results if tests_results else []
        self.styles_results = styles_results if styles_results else []
        self.coverages_results = coverages_results if coverages_results else []
        self.tier = tier
        self.configuration = configuration
        self.skip_tests = skip_tests if skip_tests is not None else False
        self.historical_test_results = historical_test_results or []
        self.stars = stars

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Transform dicrectory to Repository.

        Args:
            dictionary: dict object

        Return: Repository
        """
        tests_results = []
        if "tests_results" in dictionary:
            tests_results = [
                TestResult.from_dict(r) for r in dictionary.get("tests_results", [])
            ]
        styles_results = []
        if "styles_results" in dictionary:
            styles_results = [
                StyleResult.from_dict(r) for r in dictionary.get("styles_results", [])
            ]
        coverages_results = []
        if "coverages_results" in dictionary:
            coverages_results = [
                CoverageResult.from_dict(r)
                for r in dictionary.get("coverages_results", [])
            ]

        configuration = None
        if dictionary.get("configuration") is not None:
            configuration = RepositoryConfiguration.from_dict(
                dictionary.get("configuration")
            )

        historical_test_results = []
        if "historical_test_results" in dictionary:
            historical_test_results = [
                TestResult.from_dict(r)
                for r in dictionary.get("historical_test_results", [])
            ]

        return Repository(
            name=dictionary.get("name"),
            url=dictionary.get("url"),
            description=dictionary.get("description"),
            licence=dictionary.get("licence"),
            contact_info=dictionary.get("contact_info"),
            alternatives=dictionary.get("alternatives"),
            labels=dictionary.get("labels"),
            tier=dictionary.get("tier"),
            tests_results=tests_results,
            styles_results=styles_results,
            coverages_results=coverages_results,
            configuration=configuration,
            skip_tests=dictionary.get("skip_tests"),
            historical_test_results=historical_test_results,
            stars=dictionary.get("stars"),
        )

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
