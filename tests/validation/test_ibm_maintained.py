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
"""Tests for ecosystem/validation/checkup_ibm_maintained.py"""

# the test methods are named after the check up they cover, like [I00]
# pylint: disable=invalid-name

from ecosystem.github import GitHubData
from ecosystem.member import Member
from tests.validation import CheckupTestCase

CHECKER = "checkup_ibm_maintained.py::checkup_I00"


class TestI00(CheckupTestCase):
    """[I00] is about where an IBM-maintained project is hosted"""

    @staticmethod
    def member(ibm_maintained=True, owner="qiskit-community"):
        """A member hosted under `owner`, claiming to be IBM-maintained or not"""
        member = Member(
            name="banana",
            url=f"https://github.com/{owner or 'banana-org'}/banana-repo",
            ibm_maintained=ibm_maintained,
        )
        if owner:
            member.github = GitHubData(owner=owner, repo="banana-repo")
        return member

    def test_an_ibm_controlled_org_passes(self):
        """The three orgs IBM controls are listed in ecosystem/validation/__init__.py"""
        self.assert_records(CHECKER, set(), self.member())

    def test_the_org_is_matched_case_insensitively(self):
        """GitHub preserves the case the owner was created with"""
        self.assert_records(CHECKER, set(), self.member(owner="Qiskit"))

    def test_an_outside_org_fails(self):
        """Claiming IBM maintenance from a third-party org is the thing being caught"""
        self.assert_records(CHECKER, {"I00"}, self.member(owner="banana-org"))

    def test_a_project_nobody_claims_is_skipped(self):
        """Almost every member: the field is false by default"""
        self.assert_records(CHECKER, set(), self.member(ibm_maintained=False))

    def test_a_member_with_no_repository_is_skipped(self):
        """There is no owner to judge, which is not the same as a wrong one"""
        self.assert_records(CHECKER, set(), self.member(owner=None))
