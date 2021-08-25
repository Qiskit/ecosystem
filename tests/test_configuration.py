"""Tests for configuration files."""

from ecosystem.models import RepositoryConfiguration
from tests.common import TestCaseWithResources


class TestRepositoryConfiguration(TestCaseWithResources):
    """Tests for RepositoryConfiguration file."""

    def test_save_and_load(self):
        """Tests saving and loading of configuration,"""
        config = RepositoryConfiguration(dependencies_files=["requirements.txt",
                                                             "requirements-dev.txt"],
                                         extra_dependencies=["qiskit"],
                                         tests_command=["python -m unittest -v"],
                                         styles_check_command=["pylint -rn ecosystem tests"])
        save_path = f"{self.path}/config.json"
        config.save(save_path)

        recovered_config = RepositoryConfiguration.load(save_path)

        self.assertEqual(config.language, recovered_config.language)
        self.assertEqual(config.tests_command, recovered_config.tests_command)
        self.assertEqual(config.dependencies_files, recovered_config.dependencies_files)
        self.assertEqual(config.extra_dependencies, recovered_config.extra_dependencies)
        self.assertEqual(config.styles_check_command, recovered_config.styles_check_command)
