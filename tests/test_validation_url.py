"""Tests for URL validation helpers."""

from unittest import TestCase

from ecosystem.member import Member
from ecosystem.pypi import PyPIData
from ecosystem.validation.test_url import TestURLs as URLValidationChecks


class TestURLValidation(TestCase):
    """Unit tests for URL validation checks."""

    def test_get_all_urls_includes_packages_and_pypi_urls(self):
        """Collect package and PyPI URLs from nested member data."""
        member = Member(
            name="Qiskit Banana Compiler",
            url="https://github.com/somebody/banana-compiler",
            packages=["https://example.org/package"],
            pypi={
                "banana-compiler": PyPIData(
                    package_name="banana-compiler",
                    url="https://pypi.org/project/banana-compiler/",
                )
            },
        )

        urls = list(URLValidationChecks.get_all_urls(member))

        self.assertIn(
            ("member.packages[0]", "https://example.org/package"),
            [(path, str(url)) for path, url in urls],
        )
        self.assertIn(
            (
                "member.pypi.banana-compiler.url",
                "https://pypi.org/project/banana-compiler/",
            ),
            [(path, str(url)) for path, url in urls],
        )

    def test_duplicate_urls_rejects_website_matching_repository_url(self):
        """Reject websites that only repeat the repository URL."""
        member = Member(
            name="Qiskit Banana Compiler",
            url="https://github.com/somebody/banana-compiler",
            website="https://github.com/somebody/banana-compiler/",
        )

        with self.assertRaisesRegex(
            AssertionError, "member.url'.*member.website|member.website'.*member.url"
        ):
            URLValidationChecks().test_duplicate_urls(member)

    def test_duplicate_urls_rejects_website_matching_pypi_url(self):
        """Reject websites that only repeat the PyPI project URL."""
        member = Member(
            name="Qiskit Banana Compiler",
            url="https://github.com/somebody/banana-compiler",
            website="https://pypi.org/project/banana-compiler/",
            pypi={
                "banana-compiler": PyPIData(
                    package_name="banana-compiler",
                    url="https://pypi.org/project/banana-compiler/",
                )
            },
        )

        with self.assertRaisesRegex(
            AssertionError,
            "member.website'.*member.pypi.banana-compiler.url|"
            "member.pypi.banana-compiler.url'.*member.website",
        ):
            URLValidationChecks().test_duplicate_urls(member)

    def test_duplicate_urls_allows_distinct_urls(self):
        """Allow distinct website, documentation, and package URLs."""
        member = Member(
            name="Qiskit Banana Compiler",
            url="https://github.com/somebody/banana-compiler",
            website="https://banana-compiler.org",
            documentation="https://banana-compiler.org/docs",
            pypi={
                "banana-compiler": PyPIData(
                    package_name="banana-compiler",
                    url="https://pypi.org/project/banana-compiler/",
                )
            },
        )

        URLValidationChecks().test_duplicate_urls(member)
