"""Tests for entities."""

import unittest

from ecosystem.models import TestResult, TestType
from ecosystem.models.repository import Repository


class TestRepository(unittest.TestCase):
    """Tests repository class."""

    def test_serialization(self):
        """Tests json serialization."""
        main_repo = Repository(name="mock-qiskit-terra",
                               url="https://github.com/MockQiskit/mock-qiskit.terra",
                               description="Mock description for repo.",
                               licence="Apache 2.0",
                               labels=["mock", "tests"],
                               tests_results=[
                                   TestResult(True, '0.18.1', TestType.DEV_COMPATIBLE)
                               ])
        repo_dict = main_repo.to_dict()
        recovered = Repository.from_dict(repo_dict)
        self.assertEqual(main_repo, recovered)
        self.assertEqual(main_repo.tests_results, recovered.tests_results)
