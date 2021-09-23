"""Tests for runners."""
import os
import unittest

from ecosystem.runners import PythonTestsRunner, PythonStyleRunner


class TestPythonRunner(unittest.TestCase):
    """Tests for Python runner."""

    def setUp(self) -> None:
        current_directory = os.path.dirname(os.path.abspath(__file__))
        self.simple_project_dir = (
            f"{current_directory}/" f"../resources/simple_python_repository"
        )
        self.configured_project_dir = (
            f"{current_directory}/" f"../resources/configured_python_repository"
        )

    def tearDown(self) -> None:
        files_to_delete = ["tox.ini", "terra_version.txt"]
        for directory in [self.simple_project_dir, self.configured_project_dir]:
            for file in files_to_delete:
                if os.path.exists(f"{directory}/{file}"):
                    os.remove(f"{directory}/{file}")

    def test_tests_runner_on_simple_repo(self):
        """Simple runner test."""
        runner = PythonTestsRunner(
            "test", working_directory=self.simple_project_dir, ecosystem_deps=["qiskit"]
        )

        runner.cloned_repo_directory = self.simple_project_dir
        terra_version, result = runner.workload()

        self.assertFalse(all(r.ok for r in result))
        self.assertTrue(terra_version)

    def test_tests_runner_on_configured_repo(self):
        """Configured repo runner test."""
        runner = PythonTestsRunner(
            "test",
            working_directory=self.configured_project_dir,
            ecosystem_deps=["qiskit"],
        )

        runner.cloned_repo_directory = self.configured_project_dir
        terra_version, result = runner.workload()

        self.assertTrue(all(r.ok for r in result))
        self.assertTrue(terra_version)

    def test_styles_runner_on_configured_repo(self):
        """Simple runner test."""
        runner = PythonStyleRunner(
            "test", working_directory=self.configured_project_dir
        )

        runner.cloned_repo_directory = self.configured_project_dir
        _, result = runner.workload()

        self.assertTrue(len(result) > 0)
