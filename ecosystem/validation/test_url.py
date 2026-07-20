# This code is part of Qiskit.
#
# (C) Copyright IBM 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""URL Validations"""

from urllib.parse import urlparse

import pytest

# pylint: disable=missing-function-docstring, missing-class-docstring


class TestURLs:
    @classmethod
    def get_all_urls(cls, member):
        """recursively search for URLs in the member data"""
        for key, value in member.to_dict().items():
            if isinstance(value, str) and value.startswith("http"):
                yield getattr(member, key)
            elif hasattr(getattr(member, key), "to_dict"):
                yield from TestURLs.get_all_urls(getattr(member, key))
            else:
                continue

    @staticmethod
    def normalize_url(url):
        """Normalize URL for comparison."""

        if url is None:
            return None, None

        parsed = urlparse(str(url))

        hostname = (parsed.hostname or "").lower()

        if hostname.startswith("www."):
            hostname = hostname[4:]

        path = parsed.path.rstrip("/")

        return hostname, path

    @staticmethod
    def is_same_or_subpath(candidate, reference):
        """
        Check whether candidate duplicates or points inside reference.
        """

        candidate_host, candidate_path = TestURLs.normalize_url(candidate)

        reference_host, reference_path = TestURLs.normalize_url(reference)

        if candidate_host != reference_host:
            return False

        return candidate_path == reference_path or candidate_path.startswith(
            reference_path + "/"
        )

    def test_http(self, member):
        for url in TestURLs.get_all_urls(member):
            assert not str(url).startswith("http:"), f"{url} is not HTTPS"

    def test_025(self, member):
        """Documentation link has redundant suffix"""

        fields = ["url", "documentation", "reference_paper"]

        for field in fields:
            url = getattr(member, field)

            if url is None:
                continue

            if url.hostname.lower().endswith("readthedocs.io"):
                suffixes = [
                    "en/latest/",
                    "en/latest",
                    "en",
                ]

                for suffix in suffixes:
                    assert not url.path.endswith(
                        suffix
                    ), f"{url} has redundant suffix: {suffix}"

    def test_026(self, member):
        """The /README.md is not documentation"""

        documentation_url = getattr(member, "documentation")

        if documentation_url is None:
            pytest.skip("No member.documentation")

        if documentation_url.hostname.lower().endswith("github.com"):
            suffixes = [
                "main/README.md",
                "blob/main/README.md",
                "tree/main",
            ]

            for suffix in suffixes:
                assert not documentation_url.path.endswith(suffix), (
                    "The field `member.documentation` can be "
                    "empty. It does not have to be a link to "
                    "the repository's `README.md` or root."
                )

    def test_027(self, member):
        """Website should not duplicate GitHub or PyPI URLs"""

        website_url = getattr(member, "website")

        if website_url is None:
            pytest.skip("No member.website")

        hostname = website_url.hostname or ""

        # Reject GitHub repository URLs as website
        repository_url = getattr(member, "url")

        if repository_url is not None and repository_url.hostname.lower().endswith(
            "github.com"
        ):
            assert not TestURLs.is_same_or_subpath(
                website_url,
                repository_url,
            ), (
                "The field `member.website` should not "
                "be the GitHub repository."
            )

        assert not (
            hostname.endswith("pypi.org") or hostname.endswith("pypi.python.org")
        ), ("The field `member.website` should not point to a PyPI project URL.")
