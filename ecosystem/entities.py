"""Classes and controllers for json storage."""
import pprint
from abc import ABC
from datetime import datetime
from typing import Optional, List


# pylint: disable=too-few-public-methods
class Tier:
    """Tiers of ecosystem membership."""
    MAIN: str = "MAIN"
    MEMBER: str = "MEMBER"
    CANDIDATE: str = "CANDIDATE"


class TestType:
    """Test types for specific repository.

    Types:
    - STABLE_COMPATIBLE - compatibility of repository with stable branch of qiskit-terra
    - DEV_COMPATIBLE - compatibility if repository with dev/main branch of qiskit-terra
    - STANDARD - regular tests that comes with repo
    """
    STABLE_COMPATIBLE: str = "STABLE_COMPATIBLE"
    DEV_COMPATIBLE: str = "DEV_COMPATIBLE"
    STANDARD: str = "STANDARD"

    @classmethod
    def all(cls):
        """Return all test types"""
        return [cls.STANDARD, cls.DEV_COMPATIBLE, cls.STABLE_COMPATIBLE]


class JsonSerializable(ABC):
    """Classes that can be serialized as json."""

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Converts dict to object."""

    def to_dict(self) -> dict:
        """Converts repo to dict."""
        result = {}
        for key, val in self.__dict__.items():
            if key.startswith("_"):
                continue
            element = []
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, JsonSerializable):
                        element.append(item.to_dict())
                    else:
                        element.append(item)
            elif isinstance(val, JsonSerializable):
                element = val.to_dict()
            else:
                element = val
            result[key] = element
        return result


class TestResult(JsonSerializable):
    """Tests status."""
    _TEST_PASSED: str = "passed"
    _TEST_FAILED: str = "failed"

    def __init__(self,
                 passed: bool,
                 terra_version: str,
                 test_type: str):
        self.test_type = test_type
        self.passed = passed
        self.terra_version = terra_version

    @classmethod
    def from_dict(cls, dictionary: dict):
        return TestResult(passed=dictionary.get("passed"),
                          terra_version=dictionary.get("terra_version"),
                          test_type=dictionary.get("test_type"))

    def to_string(self) -> str:
        """Test result as string."""
        return self._TEST_PASSED if self.passed else self._TEST_FAILED

    def __eq__(self, other: 'TestResult'):
        return self.passed == other.passed \
               and self.test_type == other.test_type \
               and self.terra_version == other.terra_version

    def __repr__(self):
        return f"TestResult({self.passed}, {self.test_type}, {self.terra_version})"


class StyleResult(JsonSerializable):
    """Tests status."""
    _STYLE_PASSED: str = "passed"
    _STYLE_FAILED: str = "failed"

    def __init__(self,
                 passed: bool,
                 style_type: str):
        self.style_type = style_type
        self.passed = passed

    @classmethod
    def from_dict(cls, dictionary: dict):
        return StyleResult(passed=dictionary.get("passed"),
                           style_type=dictionary.get("test_type"))

    def to_string(self) -> str:
        """Test result as string."""
        return self._STYLE_PASSED if self.passed else self._STYLE_FAILED

    def __eq__(self, other: 'StyleResult'):
        return self.passed == other.passed \
               and self.style_type == other.style_type

    def __repr__(self):
        return f"TestResult({self.passed}, {self.style_type}"


class Repository(JsonSerializable):
    """Main repository class."""

    def __init__(self,
                 name: str,
                 url: str,
                 description: str,
                 licence: str,
                 contact_info: Optional[str] = None,
                 alternatives: Optional[str] = None,
                 affiliations: Optional[str] = None,
                 labels: Optional[List[str]] = None,
                 created_at: Optional[int] = None,
                 updated_at: Optional[int] = None,
                 tier: str = Tier.MAIN,
                 tests_results: Optional[List[TestResult]] = None):
        """Repository controller.

        Args:
            name: name of project
            url: url to github repo
            description: description
            licence: licence
            contact_info: contact information
            alternatives: alternatives to project
            affiliations : affiliations of the project
            labels: labels
            created_at: creation date
            updated_at: update date
            tests_results: tests passed by repo
        """
        self.name = name
        self.url = url
        self.description = description
        self.licence = licence
        self.contact_info = contact_info
        self.alternatives = alternatives
        self.affiliations = affiliations
        self.labels = labels if labels is not None else []
        self.created_at = created_at if created_at is not None else datetime.now().timestamp()
        self.updated_at = updated_at if updated_at is not None else datetime.now().timestamp()
        self.tests_results = tests_results if tests_results else []
        self.tier = tier

    @classmethod
    def from_dict(cls, dictionary: dict):
        tests_results = []
        if "tests_results" in dictionary:
            tests_results = [TestResult.from_dict(r) for r in dictionary.get("tests_results", [])]

        return Repository(name=dictionary.get("name"),
                          url=dictionary.get("url"),
                          description=dictionary.get("description"),
                          licence=dictionary.get("licence"),
                          contact_info=dictionary.get("contact_info"),
                          alternatives=dictionary.get("alternatives"),
                          labels=dictionary.get("labels"),
                          tier=dictionary.get("tier"),
                          tests_results=tests_results)

    def __eq__(self, other: 'Repository'):
        return (self.tier == other.tier
                and self.url == other.url
                and self.description == other.description
                and self.licence == other.licence)

    def __repr__(self):
        return pprint.pformat(self.to_dict(), indent=4)

    def __str__(self):
        return f"Repository({self.tier} | {self.name} | {self.url})"


class CommandExecutionSummary:
    """Utils for command execution results."""

    def __init__(self,
                 code: int,
                 logs: List[str],
                 summary: Optional[str] = None,
                 name: Optional[str] = None):
        """CommandExecutionSummary class."""
        self.name = name or ""
        self.code = code
        self.logs = logs
        if summary:
            self.summary = summary
        elif len(self.logs) > 0:
            self.summary = "".join(self.logs[-3:])
        else:
            self.summary = summary

    def get_warning_logs(self) -> List[str]:
        """Return warning messages."""
        return [log for log in self.logs if "warn" in log.lower()]

    @property
    def ok(self):  # pylint: disable=invalid-name
        """If command finished with success."""
        return self.code == 0

    @classmethod
    def empty(cls) -> 'CommandExecutionSummary':
        """Returns empty summary."""
        return cls(0, [])

    def __repr__(self):
        return f"CommandExecutionSummary({self.name} | code: {self.code} | {self.summary})"
