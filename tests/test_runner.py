"""Tests for runners."""
import os
import unittest

from ecosystem.controllers.runner import PythonRunner


class TestPythonRunner(unittest.TestCase):
    """Tests for Python runner."""
    def setUp(self) -> None:
        current_directory = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = f"{current_directory}/resources/python_repository"

    def tearDown(self) -> None:
        files_to_delete = ["tox.ini", "terra_version.txt"]
        for file in files_to_delete:
            if os.path.exists(f"{self.project_dir}/{file}"):
                os.remove(f"{self.project_dir}/{file}")

    def test_runner(self):
        """Simple runner test."""
        runner = PythonRunner("test",
                              working_directory=self.project_dir,
                              ecosystem_deps=["qiskit"])

        runner.cloned_repo_directory = self.project_dir
        terra_version, result = runner.workload()

        self.assertFalse(result.ok)
        self.assertTrue(terra_version)
