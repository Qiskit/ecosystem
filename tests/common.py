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
