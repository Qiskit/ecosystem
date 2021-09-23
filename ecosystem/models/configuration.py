"""Configuration for ecosystem repository."""
import json
import pprint
from typing import Optional, List

from jinja2 import Environment, PackageLoader, select_autoescape

from ecosystem.entities import JsonSerializable
from ecosystem.utils import QiskitEcosystemException


class Languages:
    """Supported configuration languages."""
    PYTHON: str = "python"

    def all(self) -> List[str]:
        """Return all supported languages."""
        return [self.PYTHON]

    def __repr__(self):
        return "Languages({})".format(",".join(self.all()))


class RepositoryConfiguration(JsonSerializable):
    """Configuration for ecosystem repository."""

    def __init__(self,
                 language: str = Languages.PYTHON,
                 dependencies_files: Optional[List[str]] = None,
                 extra_dependencies: Optional[List[str]] = None,
                 tests_command: Optional[List[str]] = None,
                 styles_check_command: Optional[List[str]] = None, ):
        """Configuration for ecosystem repository.

        Args:
            language: repository language
            dependencies_files: list of dependencies files paths relative to root of repo
                ex: for python `requirements.txt`
            extra_dependencies: list of extra dependencies for project to install during tests run
                ex: for python it might be `qiskit==0.19`
            tests_command: list of commands to run tests
                ex: for python `python -m unittest -v`
            styles_check_command: list of commands to run style checks
                ex: for python `pylint -rn ecosystem tests`
        """
        self.language = language
        self.dependencies_files = dependencies_files or []
        self.extra_dependencies = extra_dependencies or []
        self.tests_command = tests_command or []
        self.styles_check_command = styles_check_command or []

    def save(self, path: str):
        """Saves configuration as json file."""
        with open(path, "w") as json_file:
            json.dump(self.to_dict(), json_file, indent=4)

    @classmethod
    def load(cls, path: str) -> 'RepositoryConfiguration':
        """Loads json file into object."""
        with open(path, "r") as json_file:
            config: RepositoryConfiguration = json.load(
                json_file, object_hook=lambda d: RepositoryConfiguration(**d))
            if config.language == Languages.PYTHON:  # pylint: disable=no-else-return
                return PythonRepositoryConfiguration(
                    dependencies_files=config.dependencies_files,
                    extra_dependencies=config.extra_dependencies,
                    tests_command=config.tests_command,
                    styles_check_command=config.styles_check_command)
            else:
                raise QiskitEcosystemException(
                    f"Unsupported language configuration type: {config.language}")

    def __repr__(self):
        return pprint.pformat(self.to_dict(), indent=4)


class PythonRepositoryConfiguration(RepositoryConfiguration):
    """Repository configuration for python based projects."""

    def __init__(self,
                 dependencies_files: Optional[List[str]] = None,
                 extra_dependencies: Optional[List[str]] = None,
                 tests_command: Optional[List[str]] = None,
                 styles_check_command: Optional[List[str]] = None):
        super().__init__(language=Languages.PYTHON,
                         dependencies_files=dependencies_files,
                         extra_dependencies=extra_dependencies,
                         tests_command=tests_command,
                         styles_check_command=styles_check_command)
        env = Environment(
            loader=PackageLoader("ecosystem"),
            autoescape=select_autoescape()
        )
        self.tox_template = env.get_template("configured_tox.ini")
        self.lint_template = env.get_template(".pylintrc")

    @classmethod
    def default(cls) -> 'PythonRepositoryConfiguration':
        """Returns default python repository configuration."""
        return PythonRepositoryConfiguration(
            dependencies_files=[
                "requirements.txt"
            ],
            tests_command=[
                "pip check",
                "coverage run --source=. --omit=py39/*,setup.py -m pytest -W error::DeprecationWarning"
            ])

    def render_tox_file(self, directory: str = None, ecosystem_deps: List[str] = None):
        """Renders tox template from configuration."""
        ecosystem_deps = ecosystem_deps or []
        directory = directory or "."
        return self.tox_template.render({**self.to_dict(),
                                         **{'ecosystem_deps': ecosystem_deps},
                                         **{'directory': directory}})

    def render_lint_file(self, ecosystem_deps: List[str] = None):
        """Renders .pylintrc template from configuration."""
        ecosystem_deps = ecosystem_deps or []
        return self.lint_template.render({**self.to_dict(),
                                         **{'ecosystem_deps': ecosystem_deps}})
