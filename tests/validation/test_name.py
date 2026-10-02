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
"""Tests for ecosystem/validation/checkup_name.py"""

from ecosystem.member import Member
from tests.validation import CheckupTestCase

CHECKER = "checkup_name.py::checkup_010"


class TestNameCheckup(CheckupTestCase):
    """[010] is about the member name, which every member has"""

    @staticmethod
    def member(name):
        """A member called `name`"""
        return Member(name=name, url="https://github.com/banana-org/banana-repo")

    def test_010_rejects_a_name_that_looks_like_a_placeholder(self):
        """A submission named after a test run is a submission nobody meant to keep"""
        self.assert_records(CHECKER, set(), self.member("banana"))
        self.assert_records(CHECKER, {"010"}, self.member("Banana TEST repo"))
