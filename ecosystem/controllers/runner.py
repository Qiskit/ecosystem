"""Ecosystem test runner."""
import os
import shutil
from abc import abstractmethod
from logging import Logger
from typing import Dict, Optional

from ecosystem.entities import CommandExecutionSummary
from ecosystem.logging import logger as ecosystem_logger


class Runner:
    """Runner for repository checks."""

    def __init__(self,
                 working_directory: Optional[str] = None,
                 logger: Optional[Logger] = None):
        self.working_directory = working_directory or "./"
        self.logger = logger or ecosystem_logger
        self.cloned_repos_directory = "{}/cloned_repos_directory" \
                                      "".format(self.working_directory)

    def set_up(self):
        """Preparation step before running workload."""
        if self.cloned_repos_directory and \
                os.path.exists(self.cloned_repos_directory):
            shutil.rmtree(self.cloned_repos_directory)
        os.makedirs(self.cloned_repos_directory)

    def tear_down(self):
        """Execution after workload is finished."""
        if self.cloned_repos_directory and \
                os.path.exists(self.cloned_repos_directory):
            shutil.rmtree(self.cloned_repos_directory)

    @abstractmethod
    def workload(self) -> Dict[str, CommandExecutionSummary]:
        """Runs workload of commands to check repository."""

    def run(self) -> Dict[str, CommandExecutionSummary]:
        """Runs chain of commands to check repository."""
        self.set_up()
        result = self.workload()
        self.tear_down()
        return result


class PythonRunner(Runner):
    """Runners for Python repositories."""

    def __init__(self,
                 python_version: str = "py39"):
        super().__init__()
        self.template = ""
        self.python_version = python_version

    def workload(self) -> Dict[str, CommandExecutionSummary]:
        """Runs checks for python repository.

        Steps:
        - check for configuration file
        - optional: check for tox file
        - optional: render tox file
        - run tests
        - form report

        Returns: execution summary of steps
        """
