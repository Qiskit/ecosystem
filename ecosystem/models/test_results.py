"""Test results for commands."""
from __future__ import annotations
import datetime
from dataclasses import dataclass
from enum import Enum

from .utils import JsonSerializable


class TestStatus(str, Enum):
    # pylint: disable=invalid-name, missing-docstring
    PASSED = "passed"
    FAILED = "failed"


class Package:  # pylint: disable=too-few-public-methods
    """Frameworks."""

    TERRA: str = "qiskit-terra"
    NATURE: str = "qiskit-nature"
    ML: str = "qiskit-machine-learning"
    OPTIMIZATION: str = "qiskit-optimization"
    DYNAMICS: str = "qiskit-dymanics"

    def all(self) -> list[str]:
        """Returns list of all available Qiskit frameworks."""
        return [self.TERRA, self.NATURE, self.ML, self.OPTIMIZATION, self.DYNAMICS]


@dataclass
class TestResult(JsonSerializable):
    """
    Tests result class.

    Attributes:
        passed: passed or not
        test_type: dev, standard, stable
        package: framework tested against
        package_version: version of framework tested against
        logs_link: link to logs of tests
        package_commit_hash: package commit hash
    """

    passed: bool
    test_type: str
    package: str
    package_version: str
    logs_link: str | None = None
    package_commit_hash: str | None = None
    terra_version: str = None
    timestamp: float = None

    def __post_init__(self):
        self.terra_version = self.package_version
        self.timestamp = datetime.datetime.now().timestamp()

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Get result from dict.

        Args:
            dictionary: dict object with the result of tox -epy3.x

        Return: TestResult
        """
        return TestResult(**dictionary)

    def to_string(self) -> str:
        """Test result as string."""
        return TestStatus.PASSED if self.passed else TestStatus.FAILED

    def __eq__(self, other: "TestResult"):
        return (
            self.passed == other.passed
            and self.test_type == other.test_type
            and self.package == other.package
            and self.package_version == other.package_version
        )

    def __repr__(self):
        return (
            f"TestResult("
            f"{self.passed}, {self.test_type}, "
            f"{self.package}: {self.package_version})"
        )


@dataclass
class StyleResult(JsonSerializable):
    """Tests status."""

    passed: bool
    style_type: str

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Get result from dict.

        Args:
            dictionary: dict object with the result of tox -elint

        Return: StyleResult
        """
        return StyleResult(**dictionary)

    def to_string(self) -> str:
        """Style result as string."""
        return TestStatus.PASSED if self.passed else TestStatus.FAILED

    def __eq__(self, other: "StyleResult"):
        return self.passed == other.passed and self.style_type == other.style_type

    def __repr__(self):
        return f"TestResult({self.passed}, {self.style_type}"


@dataclass
class CoverageResult(JsonSerializable):
    """Tests status."""

    passed: str
    coverage_type: str

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Get result from dict.

        Args:
            dictionary: dict object with the result of tox -ecoverage

        Return: CoverageResult
        """
        return CoverageResult(**dictionary)

    def to_string(self) -> str:
        """Style result as string."""
        return TestStatus.PASSED if self.passed else TestStatus.FAILED

    def __eq__(self, other: "CoverageResult"):
        return self.passed == other.passed and self.coverage_type == other.coverage_type

    def __repr__(self):
        return f"TestResult({self.passed}, {self.coverage_type}"
