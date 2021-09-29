"""Ecosystem python coverage runner."""
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


class PythonCoverageRunner(Runner):
    """Runners for coveraging Python repositories."""

    def __init__(
        self,
        repo: Union[str, Repository],
        working_directory: Optional[str] = None,
        repo_config: Optional[RepositoryConfiguration] = None,
    ):
        super().__init__(
            repo=repo, working_directory=working_directory, repo_config=repo_config
        )

    def workload(self) -> Tuple[str, List[CommandExecutionSummary]]:
        """Runs styles checks for python repository.

        Steps:
        - check for configuration file
            - optional: check for .coveragerc file
        - optional: render .coveragerc file
            - run coverage
        - form report

        Returns: execution summary of steps
        """
        # check for configuration file
        # check for existing .coveragerc file
        # render new .coveragerc file for tests
        # check for existing tox file
        # render new tox file for tests
        config = self.get_config(
            [".coveragerc", "tox.ini"],
            [".coveragerc_default", "tox_default.ini"]
        )

        # run lint
        tox_coverage_res = RunToxCommand.execute(
            directory=self.cloned_repo_directory, env="coverage"
        )

        return "-", [tox_coverage_res]
