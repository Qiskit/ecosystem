"""Tests for configuration files."""
import os

from ecosystem.models import (
    RepositoryConfiguration,
    PythonLanguageConfiguration,
    PythonRepositoryConfiguration,
)
from tests.common import TestCaseWithResources


class TestRepositoryConfiguration(TestCaseWithResources):
    """Tests for RepositoryConfiguration file."""

    def test_save_and_load(self):
        """Tests saving and loading of configuration."""
        config = RepositoryConfiguration(
            language=PythonLanguageConfiguration(versions=["3.6"]),
            dependencies_files=["requirements.txt", "requirements-dev.txt"],
            extra_dependencies=["qiskit"],
            tests_command=["python -m unittest -v"],
            styles_check_command=["pylint -rn ecosystem tests"],
            coverages_check_command=[
                "coverage3 -m pytest",
                "coverage3 report --fail-under=80",
            ],
            depends_on_qiskit=False,
        )
        save_path = f"{self.path}/config.json"
        config.save(save_path)

        recovered_config = RepositoryConfiguration.load(save_path)

        self.assertEqual(config.language.name, recovered_config.language.name)
        self.assertEqual(config.language.versions, recovered_config.language.versions)
        self.assertEqual(config.tests_command, recovered_config.tests_command)
        self.assertEqual(config.dependencies_files, recovered_config.dependencies_files)
        self.assertEqual(config.extra_dependencies, recovered_config.extra_dependencies)
        self.assertEqual(
            config.styles_check_command, recovered_config.styles_check_command
        )
        self.assertEqual(
            config.coverages_check_command, recovered_config.coverages_check_command
        )
        self.assertFalse(recovered_config.depends_on_qiskit)

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
        for command in config.styles_check_command:
            self.assertTrue(command in rendered_tox)
        for command in config.coverages_check_command:
            self.assertTrue(command in rendered_tox)

    def test_non_complete_config_load(self):
        """Tests non full configuration load."""
        path_to_config = (
            f"{os.path.dirname(os.path.abspath(__file__))}/"
            f"../resources/test_ecosystem_config.json"
        )

        config = PythonRepositoryConfiguration.load(path_to_config)
        self.assertEqual(config.language.name, "python")
        self.assertEqual(
            config.language.versions, PythonLanguageConfiguration.default_version()
        )
        self.assertEqual(config.dependencies_files, [])
        self.assertEqual(config.tests_command, [])
        self.assertEqual(config.styles_check_command, [])
        self.assertEqual(config.extra_dependencies, [])
        self.assertTrue(config.depends_on_qiskit)
