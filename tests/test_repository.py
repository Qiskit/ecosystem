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

"""Tests for entities."""

import unittest

from ecosystem.member import Member


class TestMember(unittest.TestCase):
    """Tests Member class."""

    def test_serialization(self):
        """Tests json serialization.
        Function: Submission
                -> from_dict
        """
        main_repo = Member(
            name="mock-qiskit-terra",
            url="https://github.com/MockQiskit/mock-qiskit.terra",
            description="Mock description for repo.",
            licence="Apache 2.0",
            labels=["mock", "tests"],
            website="https://example.org",
        )
        repo_dict = main_repo.to_dict()
        recovered = Member.from_dict(repo_dict)
        self.assertEqual(main_repo, recovered)
