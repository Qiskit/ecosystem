"""Ecosystem test runner."""
import os
import shutil
from abc import abstractmethod
from logging import Logger
from typing import Optional, Union, List, Tuple, cast

from ecosystem.commands import CloneRepoCommand
from ecosystem.models import CommandExecutionSummary, RepositoryConfiguration, PythonRepositoryConfiguration
from ecosystem.models.repository import Repository
from ecosystem.utils import QiskitEcosystemException
from ecosystem.utils import logger as ecosystem_logger


def runner_ConfigFile(runner):
    """check for configuration file"""
    if runner.repo_config is not None:
        repo_config = runner.repo_config
    elif os.path.exists(f"{runner.cloned_repo_directory}/ecosystem.json"):
        runner.logger.info("Configuration file exists.")
        loaded_config = RepositoryConfiguration.load(
            f"{runner.cloned_repo_directory}/ecosystem.json"
        )
        repo_config = cast(PythonRepositoryConfiguration, loaded_config)
    else:
        repo_config = PythonRepositoryConfiguration.default()

    return repo_config


def runner_ToxFile(runner, repo_config):
    """check for Tox file"""
    if os.path.exists(f"{runner.cloned_repo_directory}/tox.ini"):
        runner.logger.info("Tox file exists.")
        os.rename(
            f"{runner.cloned_repo_directory}/tox.ini",
            f"{runner.cloned_repo_directory}/tox_default.ini",
        )

    # render new tox file for tests
    with open(f"{runner.cloned_repo_directory}/tox.ini", "w") as tox_file:
        tox_file.write(
            repo_config.render_tox_file(ecosystem_deps=runner.ecosystem_deps)
        )


class Runner:
    """Runner for repository checks.

    General class to run workflow for repository.
    """

    def __init__(
        self,
        repo: Union[str, Repository],
        working_directory: Optional[str] = None,
        repo_config: Optional[RepositoryConfiguration] = None,
        logger: Optional[Logger] = None,
    ):
        self.repo: str = repo.url if isinstance(repo, Repository) else repo
        self.working_directory = f"{working_directory}/cloned_repo_directory" or "./"
        self.logger = logger or ecosystem_logger
        name = self.repo.split("/")[-1]
        self.cloned_repo_directory = f"{self.working_directory}/{name}"
        self.repo_config = repo_config

    def set_up(self):
        """Preparation step before running workload."""
        if self.cloned_repo_directory and os.path.exists(self.cloned_repo_directory):
            shutil.rmtree(self.cloned_repo_directory)
        os.makedirs(self.cloned_repo_directory)

    def tear_down(self):
        """Execution after workload is finished."""
        if self.cloned_repo_directory and os.path.exists(self.cloned_repo_directory):
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
        clone_res = CloneRepoCommand.execute(
            repo=self.repo, directory=self.working_directory
        )

        if not clone_res.ok:
            raise QiskitEcosystemException(
                f"Something went wrong with cloning {self.repo} repository."
            )

        try:
            result = self.workload()
        except Exception as exception:  # pylint: disable=broad-except
            result = ("-", CommandExecutionSummary(1, [], summary=str(exception)))
            self.logger.error(exception)
        self.tear_down()
        return result
