"""Ecosystem python test runner."""
import os
from typing import Optional, Union, cast, List, Tuple

from ecosystem.commands import RunToxCommand
from ecosystem.models import (
    RepositoryConfiguration,
    PythonRepositoryConfiguration,
    CommandExecutionSummary,
)
from ecosystem.models.repository import Repository
from ecosystem.runners.runner import Runner


class PythonTestsRunner(Runner):
    """Runners for testing Python repositories."""

    def __init__(
        self,
        repo: Union[str, Repository],
        working_directory: Optional[str] = None,
        ecosystem_deps: Optional[List[str]] = None,
        python_version: str = "py39",
        repo_config: Optional[RepositoryConfiguration] = None,
    ):
        super().__init__(
            repo=repo, working_directory=working_directory, repo_config=repo_config
        )
        self.python_version = python_version
        self.ecosystem_deps = ecosystem_deps or ["qiskit"]

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
        config = self.get_config(["tox.ini"], ["tox_default.ini"], self.ecosystem_deps)

        terra_version = "-"
        if not os.path.exists(f"{self.cloned_repo_directory}/setup.py"):
            self.logger.error("No setup.py file for repository %s", self.repo)
            return terra_version, []

        # run tox
        tox_tests_res = RunToxCommand.execute(
            directory=self.cloned_repo_directory, env=self.python_version
        )

        # get terra version from file
        if os.path.exists(f"{self.cloned_repo_directory}/terra_version.txt"):
            with open(
                f"{self.cloned_repo_directory}/terra_version.txt", "r"
            ) as version_file:
                terra_version = version_file.read()
                self.logger.info("Terra version: %s", terra_version)
        else:
            self.logger.warning("There in no terra version file...")

        return terra_version, [tox_tests_res]
