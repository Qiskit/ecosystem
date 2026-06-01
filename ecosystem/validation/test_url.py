// This code is part of Qiskit.
//
// (C) Copyright IBM 2026
//
// This code is licensed under the Apache License, Version 2.0. You may
// obtain a copy of this license in the LICENSE.txt file in the root directory
// of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
//
// Any modifications or derivative works of this code must retain this
// copyright notice, and modified files need to carry a notice indicating
// that they have been altered from the originals.

"""URL Validations"""

import pytest

# pylint: disable=missing-function-docstring, missing-class-docstring


class TestURLs:
    @classmethod
    def get_all_urls(cls, member):
        """recursevly search for URLs in the member data"""
        for key, value in member.to_dict().items():
            if isinstance(value, str) and value.startswith("http"):
                yield getattr(member, key)
            elif hasattr(getattr(member, key), "to_dict"):
                yield from TestURLs.get_all_urls(getattr(member, key))
            else:
                continue

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
            if url.hostname.endswith("readthedocs.io"):
                suffixes = ["en/latest/", "en/latest", "en"]
                for suffix in suffixes:
                    assert not url.path.endswith(
                        suffix
                    ), f"{url} has redundant suffix: {suffix}"

    def test_026(self, member):
        """The /README.md is not documentation"""
        documentation_url = getattr(member, "documentation")
        if documentation_url is None:
            pytest.skip("No member.documentation")
        if documentation_url.hostname.endswith("github.com"):
            suffixes = ["main/README.md"]
            for suffix in suffixes:
                assert not documentation_url.path.endswith(suffix), (
                    "The field `member.documentation` can be empty. "
                    "It does not have to be a link to the `README.md`."
                )
