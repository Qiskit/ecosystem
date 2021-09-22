"""Ecosystem test runner."""
import os
import shutil
from abc import abstractmethod
from logging import Logger
from typing import Optional, Union, List, Tuple

from ecosystem.commands import _clone_repo
from ecosystem.models import CommandExecutionSummary, RepositoryConfiguration
from ecosystem.models.repository import Repository
from ecosystem.utils import QiskitEcosystemException
from ecosystem.utils import logger as ecosystem_logger


class Runner:
    """Runner for repository checks.

    General class to run workflow for repository.
    """

    def __init__(self,
                 repo: Union[str, Repository],
                 working_directory: Optional[str] = None,
                 repo_config: Optional[RepositoryConfiguration] = None,
                 logger: Optional[Logger] = None):
        self.repo: str = repo.url if isinstance(repo, Repository) else repo
        self.working_directory = f"{working_directory}/cloned_repo_directory" or "./"
        self.logger = logger or ecosystem_logger
        name = self.repo.split("/")[-1]
        self.cloned_repo_directory = f"{self.working_directory}/{name}"
        self.repo_config = repo_config

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
        except Exception as exception:  # pylint: disable=broad-except
            result = ("-", CommandExecutionSummary(1, [], summary=str(exception)))
            self.logger.error(exception)
        self.tear_down()
        return result
