"""Tests utils."""
from unittest import TestCase

from ecosystem.utils import demo


class TestUtils(TestCase):
    """Tests utils."""

    def test_demo(self):
        """Tests demo function."""
        self.assertTrue(demo())
