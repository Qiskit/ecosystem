"""Common test classes."""
import os
import shutil
import unittest


class TestCaseWithResources(unittest.TestCase):
    """Test case with additional resources folder."""
    path: str

    def setUp(self) -> None:
        self.path = "./resources"
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def tearDown(self) -> None:
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
