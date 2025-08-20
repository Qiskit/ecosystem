"""Tests for entities."""

import unittest

from ecosystem.models.repository import Repository


class TestRepository(unittest.TestCase):
    """Tests repository class."""

    def test_serialization(self):
        """Tests json serialization.
        Function: Repository
                -> from_dict
        """
        main_repo = Repository(
            name="mock-qiskit-terra",
            url="https://github.com/MockQiskit/mock-qiskit.terra",
            description="Mock description for repo.",
            licence="Apache 2.0",
            labels=["mock", "tests"],
            stars=42,
            website="https://example.org",
        )
        repo_dict = main_repo.to_dict()
        recovered = Repository.from_dict(repo_dict)
        self.assertEqual(main_repo, recovered)
        # check configs
        self.assertEqual(
            main_repo.stars,
            recovered.stars,
        )
