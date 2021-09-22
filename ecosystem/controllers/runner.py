"""Ecosystem test runner."""
import os
import shutil
from abc import abstractmethod
from logging import Logger
from typing import Optional, Union, cast, List, Tuple

from ecosystem.commands import _clone_repo, _run_tox, _run_lint
from ecosystem.entities import CommandExecutionSummary, Repository
from ecosystem.utils import logger as ecosystem_logger
from ecosystem.models import RepositoryConfiguration, PythonRepositoryConfiguration
from ecosystem.utils import QiskitEcosystemException


class Runner:
    """Runner for repository checks.

    General class to run workflow for repository.
    """

    def __init__(self,
                 repo: Union[str, Repository],
                 working_directory: Optional[str] = None,
                 logger: Optional[Logger] = None):
        self.repo: str = repo.url if isinstance(repo, Repository) else repo
        self.working_directory = f"{working_directory}/cloned_repo_directory" or "./"
        self.logger = logger or ecosystem_logger
        name = self.repo.split("/")[-1]
        self.cloned_repo_directory = f"{self.working_directory}/{name}"

    def set_up(self):
        """Preparation step before running workload."""
        if self.cloned_repo_directory and \
                os.path.exists(self.cloned_repo_directory):
            shutil.rmtree(self.cloned_repo_directory)
        os.makedirs(self.cloned_repo_directory)

    def tear_down(self):
        """Execution after workload is finished."""
        if self.cloned_repo_directory and \
                os.path.exists(self.cloned_repo_directory):
            shutil.rmtree(self.cloned_repo_directory)

    @abstractmethod
    def workload(self) -> Tuple[str, List[CommandExecutionSummary]]:
        """Runs workload of commands to check repository.

        Returns: tuple (qiskit_version, CommandExecutionSummary)
        """

    def run(self) -> Tuple[str, List[CommandExecutionSummary]]:
        """Runs chain of commands to check repository."""
        self.set_up()
        # clone repository
        self.logger.info("Cloning repository: %s", self.repo)
        clone_res = _clone_repo(self.repo, directory=self.working_directory)

        if not clone_res.ok:
            raise QiskitEcosystemException(
                f"Something went wrong with cloning {self.repo} repository.")

        try:
            result = self.workload()
        except Exception as exception:  # pylint: disable=broad-except)
            result = ("-", CommandExecutionSummary(1, [], summary=str(exception)))
            self.logger.error(exception)
        self.tear_down()
        return result


class PythonTestsRunner(Runner):
    """Runners for testing Python repositories."""

    def __init__(self,
                 repo: Union[str, Repository],
                 working_directory: Optional[str] = None,
                 ecosystem_deps: Optional[List[str]] = None,
                 python_version: str = "py39",
                 repo_config: Optional[RepositoryConfiguration] = None):
        super().__init__(repo=repo,
                         working_directory=working_directory)
        self.python_version = python_version
        self.ecosystem_deps = ecosystem_deps or ["qiskit"]
        self.repo_config = repo_config

    def workload(self) -> Tuple[str, List[CommandExecutionSummary]]:
        """Runs tests checks for python repository.

        Steps:
        - check for configuration file
        - optional: check for tox file
        - optional: render tox file
        - run tests
        - form report

        Returns: execution summary of steps
        """
        # check for configuration file
        if self.repo_config is not None:
            repo_config = self.repo_config
        elif os.path.exists(f"{self.cloned_repo_directory}/qe_config.json"):
            self.logger.info("Configuration file exists.")
            loaded_config = RepositoryConfiguration.load(
                f"{self.cloned_repo_directory}/qe_config.json")
            repo_config = cast(PythonRepositoryConfiguration, loaded_config)
        else:
            repo_config = PythonRepositoryConfiguration.default()

        # check for existing tox file
        if os.path.exists(f"{self.cloned_repo_directory}/tox.ini"):
            self.logger.info("Tox file exists.")
            os.rename(f"{self.cloned_repo_directory}/tox.ini",
                      f"{self.cloned_repo_directory}/tox_default.ini")

        # render new tox file for tests
        with open(f"{self.cloned_repo_directory}/tox.ini", "w") as tox_file:
            tox_file.write(repo_config.render_tox_file(
                ecosystem_deps=self.ecosystem_deps))

        terra_version = "-"
        if not os.path.exists(f"{self.cloned_repo_directory}/setup.py"):
            self.logger.error("No setup.py file for repository %s", self.repo)
            return terra_version, []

        # run tox
        tox_tests_res = _run_tox(directory=self.cloned_repo_directory,
                                 env=self.python_version)

        # get terra version from file
        if os.path.exists(f"{self.cloned_repo_directory}/terra_version.txt"):
            with open(f"{self.cloned_repo_directory}/terra_version.txt", "r") as version_file:
                terra_version = version_file.read()
                self.logger.info("Terra version: %s", terra_version)
        else:
            self.logger.warning("There in no terra version file...")

        return terra_version, [tox_tests_res]


class PythonStyleRunner(Runner):
    """Runners for styling Python repositories."""

    def __init__(self,
                 repo: Union[str, Repository],
                 working_directory: Optional[str] = None,
                 ecosystem_deps: Optional[List[str]] = None,
                 repo_config: Optional[RepositoryConfiguration] = None):
        super().__init__(repo=repo,
                         working_directory=working_directory)
        self.ecosystem_deps = ecosystem_deps or ["qiskit"]
        self.repo_config = repo_config

    def workload(self) -> List[CommandExecutionSummary]:
        """Runs styles checks for python repository.

        Steps:
	- check for configuration file
        - optional: check for .pylintrc file
	- optional: render .pylintrc file
        - run lint
        - form report

        Returns: execution summary of steps
        """

        # check for configuration file
        if self.repo_config is not None:
            repo_config = self.repo_config
        elif os.path.exists(f"{self.cloned_repo_directory}/qe_config.json"):
            self.logger.info("Configuration file exists.")
            loaded_config = RepositoryConfiguration.load(
                f"{self.cloned_repo_directory}/qe_config.json")
            repo_config = cast(PythonRepositoryConfiguration, loaded_config)
        else:
            repo_config = PythonRepositoryConfiguration.default()

        # check for existing .pylintrc file
        if os.path.exists(f"{self.cloned_repo_directory}/.pylintrc"):
            self.logger.info(".pylintrc file exists.")
            os.rename(f"{self.cloned_repo_directory}/.pylintrc",
                      f"{self.cloned_repo_directory}/.pylintrc_default")

        # render new tox file for tests
        with open(f"{self.cloned_repo_directory}/.pylintrc", "w") as lint_file:
            lint_file.write(repo_config.render_lint_file(
                ecosystem_deps=self.ecosystem_deps))

        # run lint
        tox_lint_res = _run_lint(directory=self.cloned_repo_directory)

        return [tox_lint_res]
