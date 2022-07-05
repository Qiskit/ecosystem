"""Test results for commands."""
import datetime
from typing import Optional, List

from .utils import JsonSerializable


class Package:  # pylint: disable=too-few-public-methods
    """Frameworks."""

    TERRA: str = "qiskit-terra"
    NATURE: str = "qiskit-nature"
    ML: str = "qiskit-machine-learning"
    OPTIMIZATION: str = "qiskit-optimization"
    DYNAMICS: str = "qiskit-dymanics"

    def all(self) -> List[str]:
        """Returns list of all available Qiskit frameworks."""
        return [self.TERRA, self.NATURE, self.ML, self.OPTIMIZATION, self.DYNAMICS]


class TestResult(JsonSerializable):
    """Tests result class."""

    _TEST_PASSED: str = "passed"
    _TEST_FAILED: str = "failed"

    def __init__(
        self,
        passed: bool,
        test_type: str,
        package: str,
        package_version: str,
        logs_link: Optional[str] = None,
        package_commit_hash: Optional[str] = None,
    ):
        """Tests result.

        Args:
            passed: passed or not
            test_type: dev, standard, stable
            package: framework tested against
            package_version: version of framework tested against
            logs_link: link to logs of tests
            package_commit_hash: package commit hash
        """
        self.test_type = test_type
        self.passed = passed
        self.package = package
        self.package_version = package_version
        self.terra_version = package_version
        self.timestamp = datetime.datetime.now().timestamp()
        self.logs_link = logs_link
        self.package_commit_hash = package_commit_hash

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Get result form dict.

        Args:
            dictionary: dict object with the result of tox -epy3.x

        Return: TestResult
        """
        return TestResult(
            passed=dictionary.get("passed"),
            test_type=dictionary.get("test_type"),
            package=dictionary.get("package"),
            package_version=dictionary.get("package_version"),
            logs_link=dictionary.get("logs_link"),
            package_commit_hash=dictionary.get("package_commit_hash"),
        )

    def to_string(self) -> str:
        """Test result as string."""
        return self._TEST_PASSED if self.passed else self._TEST_FAILED

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


class StyleResult(JsonSerializable):
    """Tests status."""

    _STYLE_PASSED: str = "passed"
    _STYLE_FAILED: str = "failed"

    def __init__(self, passed: bool, style_type: str):
        self.style_type = style_type
        self.passed = passed

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Get result form dict.

        Args:
            dictionary: dict object with the result of tox -elint

        Return: StyleResult
        """
        return StyleResult(
            passed=dictionary.get("passed"), style_type=dictionary.get("style_type")
        )

    def to_string(self) -> str:
        """Style result as string."""
        return self._STYLE_PASSED if self.passed else self._STYLE_FAILED

    def __eq__(self, other: "StyleResult"):
        return self.passed == other.passed and self.style_type == other.style_type

    def __repr__(self):
        return f"TestResult({self.passed}, {self.style_type}"


class CoverageResult(JsonSerializable):
    """Tests status."""

    _COVERAGE_PASSED: str = "passed"
    _COVERAGE_FAILED: str = "failed"

    def __init__(self, passed: bool, coverage_type: str):
        self.coverage_type = coverage_type
        self.passed = passed

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Get result form dict.

        Args:
            dictionary: dict object with the result of tox -ecoverage

        Return: CoverageResult
        """
        return CoverageResult(
            passed=dictionary.get("passed"),
            coverage_type=dictionary.get("coverage_type"),
        )

    def to_string(self) -> str:
        """Style result as string."""
        return self._COVERAGE_PASSED if self.passed else self._COVERAGE_FAILED

    def __eq__(self, other: "CoverageResult"):
        return self.passed == other.passed and self.coverage_type == other.coverage_type

    def __repr__(self):
        return f"TestResult({self.passed}, {self.coverage_type}"
