"""Configuration for ecosystem repository."""
import json
import pprint
from typing import Optional, List

from jinja2 import Environment, PackageLoader, select_autoescape

from ecosystem.utils.utils import QiskitEcosystemException
from .utils import JsonSerializable


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


class RepositoryConfiguration(JsonSerializable):
    """Configuration for ecosystem repository."""

    def __init__(
        self,
        language: Optional[LanguageConfiguration] = None,
        dependencies_files: Optional[List[str]] = None,
        extra_dependencies: Optional[List[str]] = None,
        tests_command: Optional[List[str]] = None,
        styles_check_command: Optional[List[str]] = None,
        coverages_check_command: Optional[List[str]] = None,
    ):
        """Configuration for ecosystem repository.

        Args:
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
        self.language = language or PythonLanguageConfiguration()
        self.dependencies_files = dependencies_files or []
        self.extra_dependencies = extra_dependencies or []
        self.tests_command = tests_command or []
        self.styles_check_command = styles_check_command or []
        self.coverages_check_command = coverages_check_command or []

    def save(self, path: str):
        """Saves configuration as json file."""
        with open(path, "w") as json_file:
            json.dump(self.to_dict(), json_file, indent=4)

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


class PythonRepositoryConfiguration(RepositoryConfiguration):
    """Repository configuration for python based projects."""

    def __init__(
        self,
        language: Optional[LanguageConfiguration] = None,
        dependencies_files: Optional[List[str]] = None,
        extra_dependencies: Optional[List[str]] = None,
        tests_command: Optional[List[str]] = None,
        styles_check_command: Optional[List[str]] = None,
        coverages_check_command: Optional[List[str]] = None,
    ):
        language = language or PythonLanguageConfiguration()
        super().__init__(
            language=language,
            dependencies_files=dependencies_files,
            extra_dependencies=extra_dependencies,
            tests_command=tests_command,
            styles_check_command=styles_check_command,
            coverages_check_command=coverages_check_command,
        )
        env = Environment(
            loader=PackageLoader("ecosystem"), autoescape=select_autoescape()
        )
        self.tox_template = env.get_template("configured_tox.ini")
        self.lint_template = env.get_template(".pylintrc")
        self.cov_template = env.get_template(".coveragerc")

    @classmethod
    def default(cls) -> "PythonRepositoryConfiguration":
        """Returns default python repository configuration."""
        return PythonRepositoryConfiguration(
            language=PythonLanguageConfiguration(),
            dependencies_files=["requirements.txt"],
            extra_dependencies=["pytest", "coverage"],
            tests_command=["pip check", "pytest"],  # -W error::DeprecationWarning
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
        return self.tox_template.render(
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
        return self.lint_template.render()

    def render_cov_file(self):
        """Renders .coveragerc template from configuration."""
        return self.cov_template.render()
