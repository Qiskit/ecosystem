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
"""Tests for ecosystem/validation/checkup_julia.py"""

# the test methods are named after the check up they cover, like [J00], and a name
# that states what the case asserts needs no docstring saying it again
# pylint: disable=invalid-name,missing-function-docstring

from contextlib import redirect_stdout
from io import StringIO

from ecosystem.julia import JuliaData
from ecosystem.member import Member
from ecosystem.validation import validate_member
from tests.validation import CheckupTestCase


class JuliaCheckupsTestCase(CheckupTestCase):
    """The sections are built the way a member file is read back, with no registry access"""

    @staticmethod
    def member(**section):
        """A member registering one Julia package"""
        member = Member(name="banana", url="https://github.com/banana-org/Banana.jl")
        member.julia = [JuliaData(package_name="Banana", version="1.0.0", **section)]
        return member


class TestJ00(JuliaCheckupsTestCase):
    """[J00] wants the registered package to declare a license"""

    checker = "checkup_julia.py::checkup_J00"

    def test_a_declared_license_passes(self):
        self.assert_records(self.checker, set(), self.member(license="MIT"))

    def test_no_license_fails(self):
        self.assert_records(self.checker, {"J00"}, self.member())


class TestJ01(JuliaCheckupsTestCase):
    """[J01] wants that license to be OSI-approved"""

    checker = "checkup_julia.py::checkup_J01"

    def test_an_osi_approved_license_passes(self):
        self.assert_records(self.checker, set(), self.member(license="MIT"))

    def test_a_source_available_license_fails(self):
        self.assert_records(
            self.checker, {"J01"}, self.member(license="PolyForm-Strict-1.0.0")
        )

    def test_no_license_is_nothing_to_judge(self):
        """[J00] is the one that complains about a missing license"""
        self.assert_records(self.checker, set(), self.member())


class TestAMemberWithNoJuliaPackage(JuliaCheckupsTestCase):
    """Almost every member: the section is absent, so both check ups have nothing to read"""

    def test_nothing_is_recorded(self):
        member = Member(name="banana", url="https://github.com/banana-org/banana-repo")
        self.assert_records("checkup_julia.py", set(), member)

    def test_the_check_ups_are_skipped_rather_than_passed(self):
        """`member.julia` defaults to `[]`, so the fixture has to test for empty.

        Testing for None let every check up run over nothing and report a pass, which said
        a project that publishes nothing had passed the checks on what it publishes.
        """
        member = Member(name="banana", url="https://github.com/banana-org/banana-repo")
        with redirect_stdout(StringIO()):
            report = validate_member(
                member, tests_to_run="checkup_julia.py", verbose_level="-q"
            )

        self.assertEqual([], report.passed)
