"""Ecosystem python styles runner."""
from typing import Optional, Union, List, Tuple

from ecosystem.commands import RunToxCommand
from ecosystem.models import (
    RepositoryConfiguration,
    CommandExecutionSummary,
)
from ecosystem.models.repository import Repository
from ecosystem.runners.runner import Runner


class PythonStyleRunner(Runner):
    """Runners for styling Python repositories."""

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
            - optional: check for .pylintrc file
        - optional: render .pylintrc file
            - run lint
        - form report

        Returns: execution summary of steps
        """
        # check for configuration file
        # check for existing .pylintrc file
        # render new .pylintrc file for tests
        # check for existing tox file
        # render new tox file for tests
        self.get_config(
            [".pylintrc", "tox.ini"], [".pylintrc_default", "tox_default.ini"]
        )

        # run lint
        tox_lint_res = RunToxCommand.execute(
            directory=self.cloned_repo_directory, env="lint"
        )

        return "-", [tox_lint_res]
