"""Docstring."""
import unittest
import warnings

from src import Random


class TestRandom(unittest.TestCase):
    """Tests Random class implementation."""

    def test_run(self):
        """Tests run method random."""
        random = Random()

        warnings.warn("test warning", DeprecationWarning)
        self.assertEqual(random.run(2), 4)
