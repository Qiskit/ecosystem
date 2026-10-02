# This code is part of Qiskit.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""Tests for ecosystem/validation/checkup_url.py"""

# a test method whose name states what the case asserts needs no docstring saying it again
# pylint: disable=missing-function-docstring

from ecosystem.github import GitHubData
from ecosystem.member import Member
from tests.validation import CheckupTestCase


class URLCheckupsTestCase(CheckupTestCase):
    """Every URL a member stores, in the fields and in the sections"""

    @staticmethod
    def member(**fields):
        """A member whose links are whatever the test needs them to be"""
        github_fields = {key: fields.pop(key) for key in ("homepage",) if key in fields}
        member = Member(
            name="banana",
            url="https://github.com/banana-org/banana-repo",
            **fields,
        )
        member.github = GitHubData(
            owner="banana-org", repo="banana-repo", **github_fields
        )
        return member


class Test013(URLCheckupsTestCase):
    """[013] wants every URL to be HTTPS"""

    checker = "checkup_url.py::CheckupURLs::checkup_013"

    def test_https_everywhere_passes(self):
        self.assert_records(self.checker, set(), self.member())

    def test_a_plain_http_link_in_a_section_fails(self):
        """A `URL` field normalizes its own scheme, so what is left to catch is a
        string stored in a section, like the repository homepage"""
        self.assert_records(
            self.checker, {"013"}, self.member(homepage="http://banana-org.example")
        )


class Test025(URLCheckupsTestCase):
    """[025] wants documentation links without a redundant Read the Docs suffix"""

    checker = "checkup_url.py::CheckupURLs::checkup_025"

    def test_the_bare_readthedocs_link_passes(self):
        self.assert_records(
            self.checker,
            set(),
            self.member(documentation="https://banana.readthedocs.io/"),
        )

    def test_the_default_version_suffix_fails(self):
        """`en/latest` is what the project's own sidebar links to, and it rots"""
        self.assert_records(
            self.checker,
            {"025"},
            self.member(documentation="https://banana.readthedocs.io/en/latest/"),
        )

    def test_other_hosts_are_not_judged(self):
        """The suffixes only mean anything on Read the Docs"""
        self.assert_records(
            self.checker,
            set(),
            self.member(
                documentation="https://banana-org.github.io/banana-repo/en/latest/",
                reference_paper="https://arxiv.org/abs/2609.00000",
            ),
        )


class Test026(URLCheckupsTestCase):
    """[026] wants documentation that is not just the repository"""

    checker = "checkup_url.py::CheckupURLs::checkup_026"

    def test_a_documentation_site_passes(self):
        self.assert_records(
            self.checker,
            set(),
            self.member(documentation="https://banana-org.github.io/banana-repo/"),
        )

    def test_the_readme_fails(self):
        self.assert_records(
            self.checker,
            {"026"},
            self.member(
                documentation="https://github.com/banana-org/banana-repo/blob/main/README.md"
            ),
        )

    def test_the_repository_root_fails(self):
        self.assert_records(
            self.checker,
            {"026"},
            self.member(
                documentation="https://github.com/banana-org/banana-repo/tree/main"
            ),
        )

    def test_no_documentation_is_skipped(self):
        """The field is allowed to be empty, which is the point of [026]"""
        self.assert_records(self.checker, set(), self.member())


class Test027(URLCheckupsTestCase):
    """[027] wants a website that is not a page the ecosystem already links to"""

    checker = "checkup_url.py::CheckupURLs::checkup_027"

    def test_a_project_site_passes(self):
        self.assert_records(
            self.checker, set(), self.member(website="https://banana.example")
        )

    def test_the_github_repository_fails(self):
        self.assert_records(
            self.checker,
            {"027"},
            self.member(website="https://github.com/banana-org/banana-repo"),
        )

    def test_the_pypi_project_page_fails(self):
        self.assert_records(
            self.checker,
            {"027"},
            self.member(website="https://pypi.org/project/banana/"),
        )

    def test_no_website_is_skipped(self):
        self.assert_records(self.checker, set(), self.member())
