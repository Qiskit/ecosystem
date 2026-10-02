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

"""Shared tooling for the check-up tests"""

from contextlib import redirect_stdout
from io import StringIO
from unittest import TestCase


class CheckupTestCase(TestCase):
    """A check up exercised the way a daily run does: one checker over a stored member.

    The members these build carry stored values only, so nothing here reaches the network.
    """

    def records(self, checker, member):
        """The ids of the check ups `checker` records on `member`"""
        with redirect_stdout(StringIO()):
            member.update_checkups(checker)
        return set(member.checks)

    def assert_records(self, checker, expected, member):
        """`checker` records exactly `expected` on `member`"""
        self.assertEqual(expected, self.records(checker, member))
