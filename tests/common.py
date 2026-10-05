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

"""Common test classes."""

import os
import shutil
import unittest


def names(sections):
    """The names of a package section, which is an array of tables.

    What `list(member.pypi)` used to give when the sections were keyed by name.
    """
    return [section.package_name for section in sections]


def named(sections, package_name):
    """The entry of a package section that carries `package_name`.

    What `member.pypi[name]` used to be. Raises rather than returning None: a test asking
    for an entry by name is asserting that it is there.
    """
    for section in sections:
        if section.package_name == package_name:
            return section
    raise KeyError(f"{package_name} is not among {names(sections)}")


class TestCaseWithResources(unittest.TestCase):
    """Test case with additional resources folder."""

    path: str

    def setUp(self) -> None:
        self.path = "./resources/tests_tmp_data"
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def tearDown(self) -> None:
        if os.path.exists(self.path):
            shutil.rmtree(self.path)


def record(member, checkup_id, subtest=None):
    """The record a check up holds on a member, when there is only one of it.

    What `member.checks[id]` used to be, before a check up that reads several places kept a
    record per place. `subtest` picks one of several by the place it is about.
    """
    records = member.checks[checkup_id]
    if subtest is not None:
        for stored in records:
            if stored.subtest == subtest:
                return stored
        raise KeyError(f"{checkup_id} has no record about {subtest}")
    if len(records) != 1:
        raise KeyError(f"{checkup_id} has {len(records)} records, not one")
    return records[0]
