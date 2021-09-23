"""Ecosystem python styles runner."""
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
        if self.repo_config is not None:
            repo_config = self.repo_config
        elif os.path.exists(f"{self.cloned_repo_directory}/qe_config.json"):
            self.logger.info("Configuration file exists.")
            loaded_config = RepositoryConfiguration.load(
                f"{self.cloned_repo_directory}/qe_config.json"
            )
            repo_config = cast(PythonRepositoryConfiguration, loaded_config)
        else:
            repo_config = PythonRepositoryConfiguration.default()

        # check for existing .pylintrc file
        if os.path.exists(f"{self.cloned_repo_directory}/.pylintrc"):
            self.logger.info(".pylintrc file exists.")
            os.rename(
                f"{self.cloned_repo_directory}/.pylintrc",
                f"{self.cloned_repo_directory}/.pylintrc_default",
            )

        # render new tox file for tests
        with open(f"{self.cloned_repo_directory}/.pylintrc", "w") as lint_file:
            lint_file.write(repo_config.render_lint_file())

        # check for existing tox file
        if os.path.exists(f"{self.cloned_repo_directory}/tox.ini"):
            self.logger.info("Tox file exists.")
            os.rename(
                f"{self.cloned_repo_directory}/tox.ini",
                f"{self.cloned_repo_directory}/tox_default.ini",
            )

        # render new tox file for tests
        with open(f"{self.cloned_repo_directory}/tox.ini", "w") as tox_file:
            tox_file.write(repo_config.render_tox_file(ecosystem_deps=[]))

        # run lint
        tox_lint_res = RunToxCommand.execute(
            directory=self.cloned_repo_directory, env="lint"
        )

        return "-", [tox_lint_res]
