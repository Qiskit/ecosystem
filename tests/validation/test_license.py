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
"""Tests for ecosystem/validation/checkup_license.py"""

# the test methods are named after the check up they cover, like [O01], and a name
# that states what the case asserts needs no docstring saying it again
# pylint: disable=invalid-name,missing-function-docstring

from ecosystem.github import GitHubData
from ecosystem.member import Member
from tests.validation import CheckupTestCase


class LicenseCheckupsTestCase(CheckupTestCase):
    """The license can be stored on the member or read off the repository"""

    @staticmethod
    def member(license=None, github_license=None, github=True):
        # pylint: disable=redefined-builtin
        """A member licensed by its own field, by its repository, or by neither"""
        member = Member(
            name="banana",
            url="https://github.com/banana-org/banana-repo",
            license=license,
        )
        if github:
            member.github = GitHubData(
                owner="banana-org",
                repo="banana-repo",
                **({"license": github_license} if github_license else {}),
            )
        return member


class TestO01(LicenseCheckupsTestCase):
    """[O01] wants a license from somewhere"""

    checker = "checkup_license.py::checkup_O01"

    def test_the_member_field_is_enough(self):
        """Which is where a submission declares it"""
        self.assert_records(self.checker, set(), self.member(license="Apache-2.0"))

    def test_the_repository_license_is_enough(self):
        """GitHub detected one, so there is a license even if nobody recorded it"""
        self.assert_records(
            self.checker, set(), self.member(github_license="Apache-2.0")
        )

    def test_neither_is_a_failure(self):
        """The member is past being new, and still nothing says how it is licensed"""
        self.assert_records(self.checker, {"O01"}, self.member())

    def test_a_new_submission_is_too_early_to_judge(self):
        """No license and no repository data yet, so the check up skips"""
        self.assert_records(self.checker, set(), self.member(github=False))


class TestO02(LicenseCheckupsTestCase):
    """[O02] wants that license to be OSI-approved"""

    checker = "checkup_license.py::checkup_O02"

    def test_an_osi_approved_license_passes(self):
        self.assert_records(self.checker, set(), self.member(license="Apache-2.0"))

    def test_a_source_available_license_fails(self):
        self.assert_records(
            self.checker, {"O02"}, self.member(license="PolyForm-Strict-1.0.0")
        )

    def test_no_stored_license_is_nothing_to_judge(self):
        """[O01] is the one that complains about a missing license"""
        self.assert_records(self.checker, set(), self.member())
