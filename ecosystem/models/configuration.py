"""Configuration for ecosystem repository."""
import json
import pprint
from typing import Optional, List
from dataclasses import dataclass, field

from jinja2 import Environment, PackageLoader, select_autoescape, Template

from ecosystem.exception import QiskitEcosystemException
from .utils import JsonSerializable, new_list


class Languages:
    """Supported configuration languages."""

    PYTHON: str = "python"

    def all(self) -> List[str]:
        """Return all supported languages."""
        return [self.PYTHON]

    def __repr__(self):
        return "Languages({})".format(",".join(self.all()))


class LanguageConfiguration(JsonSerializable):
    """Language configuration class."""

    def __init__(self, name: str, versions: List[str]):
        """Language configuration.

        Args:
            name: programming language
            versions: versions of programming languages
        """
        self.name = name
        self.versions = versions

    @classmethod
    def default_version(cls) -> List[str]:
        """Default language versions."""
        return []


class PythonLanguageConfiguration(LanguageConfiguration):
    """Python language config."""

    def __init__(self, versions: Optional[List[str]] = None):
        versions = versions or ["3.6", "3.7", "3.8", "3.9"]
        super().__init__(name=Languages.PYTHON, versions=versions)

    @classmethod
    def default_version(cls) -> List[str]:
        return ["3.6", "3.7", "3.8", "3.9"]


@dataclass
class RepositoryConfiguration(JsonSerializable):
    """
    Configuration for ecosystem repository.

    Attributes:
        language: repository language configuration
        dependencies_files: list of dependencies files paths relative to root of repo
            ex: for python `requirements.txt`
        extra_dependencies: list of extra dependencies for project to install during tests run
            ex: for python it might be `qiskit==0.19`
        tests_command: list of commands to run tests
            ex: for python `python -m unittest -v`
        styles_check_command: list of commands to run style checks
            ex: for python `pylint -rn ecosystem tests`
        coverages_check_command: list of commands to run coverage checks
            ex: for python `coverage3 -m unittest -v && coverage report`
    """

    language: LanguageConfiguration = field(default_factory=PythonLanguageConfiguration)
    dependencies_files: List[str] = new_list()
    extra_dependencies: List[str] = new_list()
    tests_command: List[str] = new_list()
    styles_check_command: List[str] = new_list()
    coverages_check_command: List[str] = new_list()

    def save(self, path: str):
        """Saves configuration as json file."""
        with open(path, "w") as json_file:
            json.dump(self.to_dict(), json_file, indent=4)

    @classmethod
    def from_dict(cls, dictionary: dict):
        if dictionary.get("language"):
            language = LanguageConfiguration(**dictionary.get("language"))
        else:
            language = PythonLanguageConfiguration()
        dictionary["language"] = language
        config: RepositoryConfiguration = RepositoryConfiguration(**dictionary)
        if config.language.name == Languages.PYTHON:  # pylint: disable=no-else-return
            return PythonRepositoryConfiguration(
                language=language,
                dependencies_files=config.dependencies_files,
                extra_dependencies=config.extra_dependencies,
                tests_command=config.tests_command,
                styles_check_command=config.styles_check_command,
                coverages_check_command=config.coverages_check_command,
            )
        else:
            raise QiskitEcosystemException(
                f"Unsupported language configuration type: {config.language}"
            )

    @classmethod
    def load(cls, path: str) -> "RepositoryConfiguration":
        """Loads json file into object."""
        with open(path, "r") as json_file:
            json_data = json.load(json_file)
            if json_data.get("language"):
                language = LanguageConfiguration(**json_data.get("language"))
            else:
                language = PythonLanguageConfiguration()
            json_data["language"] = language
            config: RepositoryConfiguration = RepositoryConfiguration(**json_data)
            if (  # pylint: disable=no-else-return
                config.language.name == Languages.PYTHON
            ):
                return PythonRepositoryConfiguration(
                    language=language,
                    dependencies_files=config.dependencies_files,
                    extra_dependencies=config.extra_dependencies,
                    tests_command=config.tests_command,
                    styles_check_command=config.styles_check_command,
                    coverages_check_command=config.coverages_check_command,
                )
            else:
                raise QiskitEcosystemException(
                    f"Unsupported language configuration type: {config.language}"
                )

    def __repr__(self):
        return pprint.pformat(self.to_dict(), indent=4)


@dataclass
class PythonRepositoryConfiguration(RepositoryConfiguration):
    """
    Repository configuration for python based projects.
    """

    _tox_template: Template = None
    _lint_template: Template = None
    _cov_template: Template = None
    _setup_template: Template = None

    def __post_init__(self):
        env = Environment(
            loader=PackageLoader("ecosystem"), autoescape=select_autoescape()
        )
        self._tox_template = env.get_template("configured_tox.ini")
        self._lint_template = env.get_template(".pylintrc")
        self._cov_template = env.get_template(".coveragerc")
        self._setup_template = env.get_template("setup.py")

    @classmethod
    def default(cls) -> "PythonRepositoryConfiguration":
        """Returns default python repository configuration."""
        return PythonRepositoryConfiguration(
            language=PythonLanguageConfiguration(),
            dependencies_files=["requirements.txt"],
            extra_dependencies=["pytest", "coverage"],
            tests_command=["pytest"],  # -W error::DeprecationWarning
            styles_check_command=["pylint -rn . tests"],
            coverages_check_command=[
                "coverage3 run -m pytest",
                "coverage3 report --fail-under=80",
            ],
        )

    def render_tox_file(
        self,
        ecosystem_deps: List[str] = None,
        ecosystem_additional_commands: List[str] = None,
    ):
        """Renders tox template from configuration."""
        ecosystem_deps = ecosystem_deps or []
        ecosystem_additional_commands = ecosystem_additional_commands or []
        return self._tox_template.render(
            {
                **self.to_dict(),
                **{
                    "ecosystem_deps": ecosystem_deps,
                    "ecosystem_additional_commands": ecosystem_additional_commands,
                },
            }
        )

    def render_lint_file(self):
        """Renders .pylintrc template from configuration."""
        return self._lint_template.render()

    def render_cov_file(self):
        """Renders .coveragerc template from configuration."""
        return self._cov_template.render()

    def render_setup_file(self):
        """Renders default setup.py file."""
        return self._setup_template.render()
