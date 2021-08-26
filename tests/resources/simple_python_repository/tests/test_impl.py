"""Docstring."""
import unittest
import warnings

from qlib import Impl


class TestImpl(unittest.TestCase):
    """Tests Impl class implementation."""

    def test_run(self):
        """Tests run method implementation."""
        impl = Impl()

        warnings.warn("test warning", DeprecationWarning)
        self.assertEqual(impl.run(2), 4)
