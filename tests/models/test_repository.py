"""Tests for entities."""

import unittest

from ecosystem.member import Member


class TestRepository(unittest.TestCase):
    """Tests repository class."""

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
            stars=42,
            website="https://example.org",
        )
        repo_dict = main_repo.to_dict()
        recovered = Member.from_dict(repo_dict)
        self.assertEqual(main_repo, recovered)
        # check configs
        self.assertEqual(
            main_repo.stars,
            recovered.stars,
        )
