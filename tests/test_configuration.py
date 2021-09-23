"""Tests for configuration files."""

from ecosystem.models import RepositoryConfiguration, PythonRepositoryConfiguration
from tests.common import TestCaseWithResources


class TestRepositoryConfiguration(TestCaseWithResources):
    """Tests for RepositoryConfiguration file."""

    def test_save_and_load(self):
        """Tests saving and loading of configuration,"""
        config = RepositoryConfiguration(dependencies_files=["requirements.txt",
                                                             "requirements-dev.txt"],
                                         extra_dependencies=["qiskit"],
                                         tests_command=["coverage run --source=. --omit=py39/*,setup.py -m pytest"],
                                         styles_check_command=["pylint -rn ecosystem tests"])
        save_path = f"{self.path}/config.json"
        config.save(save_path)

        recovered_config = RepositoryConfiguration.load(save_path)

        self.assertEqual(config.language, recovered_config.language)
        self.assertEqual(config.tests_command, recovered_config.tests_command)
        self.assertEqual(config.dependencies_files, recovered_config.dependencies_files)
        self.assertEqual(config.extra_dependencies, recovered_config.extra_dependencies)
        self.assertEqual(config.styles_check_command, recovered_config.styles_check_command)

    def test_python_configuration(self):
        """Tests python configurations."""
        config = PythonRepositoryConfiguration.default()
        rendered_tox = config.render_tox_file()
        self.assertTrue(config)
        for command in config.tests_command:
            self.assertTrue(command in rendered_tox)
        for dep in config.extra_dependencies:
            self.assertTrue(dep in rendered_tox)
        for dep_file in config.dependencies_files:
            self.assertTrue(dep_file in rendered_tox)
