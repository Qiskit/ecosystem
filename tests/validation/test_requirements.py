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
"""Tests for ecosystem/validation/checkup_requirements.py"""

# the test methods are named after the check up they cover, like [R01]
# pylint: disable=invalid-name

from contextlib import redirect_stdout
from io import StringIO
from unittest import TestCase

from ecosystem.github import GitHubData
from ecosystem.member import Member
from ecosystem.requirements import RequirementsData


class RequirementsCheckupsTestCase(TestCase):
    """Shared setup for the ecosystem/validation/checkup_requirements.py check ups.

    The sections are built the way a member file is read back: stored values only, no
    requirements file, so nothing here reaches the network.
    """

    @staticmethod
    def member(*sections, **section):
        """A member whose repository declares its qiskit dependency in a file

        Takes either sections already built, for a member that has several, or the
        keywords of the single `requirements.txt` section most of these need.
        """
        member = Member(
            name="banana",
            url="https://github.com/qiskit-community/banana-notebooks",
            description="Banana description.",
            license="Apache-2.0",
            maturity="experimental",
        )
        member.github = GitHubData(owner="qiskit-community", repo="banana-notebooks")
        member.requirements = list(sections) or [
            RequirementsData(file="requirements.txt", **section)
        ]
        return member

    def checkups_of(self, checker, *sections, **section):
        """The ids of the check ups that `checker` records on such a member"""
        member = self.member(*sections, **section)
        with redirect_stdout(StringIO()):
            member.update_checkups(checker)
        return set(member.checks)

    def assert_records(self, checker, expected, *sections, **section):
        """`checker` records exactly `expected` on a member with such sections"""
        self.assertEqual(expected, self.checkups_of(checker, *sections, **section))


class TestRequirementsCheckups(RequirementsCheckupsTestCase):
    """Each check up reads the stored section, as a daily run does"""

    def test_a_member_with_no_requirements_section_is_skipped(self):
        """Almost every member: it declares a distribution instead, or nothing"""
        member = Member(
            name="banana",
            url="https://github.com/qiskit-community/banana-notebooks",
            maturity="experimental",
        )
        with redirect_stdout(StringIO()):
            member.update_checkups("checkup_requirements.py")
        self.assertEqual(set(), set(member.checks))

    def test_R01_wants_the_requirements_file_to_allow_qiskit_v2(self):
        """The file is the only thing the repository says, so it is what is read"""
        checker = "checkup_requirements.py::checkup_R01"
        self.assert_records(checker, set(), requires_qiskit=">=1.4,<3")
        self.assert_records(checker, {"R01"}, requires_qiskit="==1.4")

    def test_R01_skips_a_section_with_nothing_to_resolve(self):
        """A stored table with no flag is not a failure to be compatible"""
        self.assert_records("checkup_requirements.py::checkup_R01", set())

    def test_R02_wants_a_cap_on_the_qiskit_major_version(self):
        """An uncapped requirement lets the next major version in untested"""
        checker = "checkup_requirements.py::checkup_R02"
        self.assert_records(checker, set(), requires_qiskit="~=2.1.0")
        self.assert_records(checker, {"R02"}, requires_qiskit=">=2.1.0")

    def test_the_failure_message_names_the_file(self):
        """A maintainer reading the project page needs to know what to edit"""
        member = self.member(requires_qiskit=">=2.1.0")
        with redirect_stdout(StringIO()):
            member.update_checkups("checkup_requirements.py::checkup_R02")
        self.assertIn("requirements.txt", member.checks["R02"].details)


class TestWhichSectionIsJudged(RequirementsCheckupsTestCase):
    """A member can store several files, and only the primary one is a declaration"""

    @staticmethod
    def sections(requires_qiskit="~=2.1.0"):
        """A lint file asking for a bare `qiskit`, beside the real requirement

        The shape `Qiskit/qiskit-cpp` has: reading the dev file as a declaration would
        say the project allows an unreleased Qiskit 3.
        """
        return [
            RequirementsData(file="requirements-dev.txt", requires_qiskit=">=0"),
            RequirementsData(
                file="requirements.txt", primary=True, requires_qiskit=requires_qiskit
            ),
        ]

    def test_the_other_files_are_stored_but_not_judged(self):
        """Both check ups read `primary_of`, so the dev file costs the member nothing"""
        self.assert_records("checkup_requirements.py", set(), *self.sections())

    def test_the_primary_file_is_what_fails(self):
        """And the message names it, not whichever file came first"""
        member = self.member(*self.sections(requires_qiskit="==1.4"))
        with redirect_stdout(StringIO()):
            member.update_checkups("checkup_requirements.py::checkup_R01")
        self.assertIn("requirements.txt", member.checks["R01"].details)
        self.assertNotIn("requirements-dev.txt", member.checks["R01"].details)
