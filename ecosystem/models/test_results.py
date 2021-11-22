"""Test results for commands."""
import datetime

from .utils import JsonSerializable


class TestResult(JsonSerializable):
    """Tests status."""

    _TEST_PASSED: str = "passed"
    _TEST_FAILED: str = "failed"

    def __init__(self, passed: bool, terra_version: str, test_type: str):
        self.test_type = test_type
        self.passed = passed
        self.terra_version = terra_version
        self.timestamp = datetime.datetime.now().timestamp()

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Get result form dict.

        Args:
            dictionary: dict object with the result of tox -epy3.x

        Return: TestResult
        """
        return TestResult(
            passed=dictionary.get("passed"),
            terra_version=dictionary.get("terra_version"),
            test_type=dictionary.get("test_type"),
        )

    def to_string(self) -> str:
        """Test result as string."""
        return self._TEST_PASSED if self.passed else self._TEST_FAILED

    def __eq__(self, other: "TestResult"):
        return (
            self.passed == other.passed
            and self.test_type == other.test_type
            and self.terra_version == other.terra_version
        )

    def __repr__(self):
        return f"TestResult({self.passed}, {self.test_type}, {self.terra_version})"


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
