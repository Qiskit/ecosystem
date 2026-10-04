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
"""Tests for ecosystem/validation/checkup_python.py"""

# the test methods are named after the check up they cover, like [S00]
# pylint: disable=invalid-name

from contextlib import redirect_stdout
from io import StringIO
from unittest import TestCase

from ecosystem.github import GitHubData
from ecosystem.member import Member
from ecosystem.python import PythonData


class PythonCheckupsTestCase(TestCase):
    """Shared setup for the ecosystem/validation/checkup_python.py check ups.

    The sections are built the way a member file is read back: stored values only, no
    manifests, so nothing here reaches the network.
    """

    @staticmethod
    def member(**section):
        """A member whose repository declares one distribution"""
        member = Member(
            name="banana",
            url="https://github.com/qiskit-community/banana-repo",
            description="Banana description.",
            license="Apache-2.0",
            maturity="experimental",
        )
        member.github = GitHubData(owner="qiskit-community", repo="banana-repo")
        member.python = [
            PythonData(
                package_name="banana-compiler",
                source=["pyproject.toml"],
                deferred=[],
                **section,
            )
        ]
        return member

    def checkups_of(self, checker, **section):
        """The ids of the check ups that `checker` records on such a member"""
        member = self.member(**section)
        with redirect_stdout(StringIO()):
            member.update_checkups(checker)
        return set(member.checks)

    def assert_records(self, checker, expected, **section):
        """`checker` records exactly `expected` on a member with such a section"""
        self.assertEqual(expected, self.checkups_of(checker, **section))


class TestPythonCheckups(PythonCheckupsTestCase):
    """Each check up reads the stored section, as a daily run does"""

    def test_a_member_with_no_python_section_is_skipped(self):
        """Nothing is declared in the repository, so there is nothing to check"""
        member = Member(
            name="banana",
            url="https://github.com/qiskit-community/banana-repo",
            maturity="experimental",
        )
        with redirect_stdout(StringIO()):
            member.update_checkups("checkup_python.py")
        self.assertEqual(set(), set(member.checks))

    def test_S00_wants_the_declared_license_to_be_osi_approved(self):
        """The declared license is matched against the OSI-approved SPDX ids"""
        checker = "checkup_python.py::checkup_S00"
        self.assert_records(checker, set(), license="Apache-2.0")
        self.assert_records(checker, {"S00"}, license="PolyForm-Strict-1.0.0")

    def test_S00_skips_a_distribution_that_declares_no_license(self):
        """The repository is what gets installed, and [G09] asks it for a license"""
        self.assert_records("checkup_python.py::checkup_S00", set())

    def test_S01_wants_the_source_to_allow_qiskit_v2(self):
        """A release can be v2-compatible while the repository has moved on, or back"""
        checker = "checkup_python.py::checkup_S01"
        self.assert_records(checker, set(), requires_qiskit=">=1.4,<3")
        self.assert_records(checker, {"S01"}, requires_qiskit=">=1.4,<2")

    def test_S01_skips_a_distribution_that_does_not_depend_on_qiskit(self):
        """No requirement is not an incompatible requirement"""
        self.assert_records("checkup_python.py::checkup_S01", set())

    def test_S02_wants_a_cap_on_the_qiskit_major_version(self):
        """An uncapped requirement lets the next major version in untested"""
        checker = "checkup_python.py::checkup_S02"
        self.assert_records(checker, set(), requires_qiskit=">=1.0,<3")
        self.assert_records(checker, {"S02"}, requires_qiskit=">=1.0")
