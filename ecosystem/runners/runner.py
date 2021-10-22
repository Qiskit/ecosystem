"""Ecosystem test runner."""
import os
import shutil
from abc import abstractmethod
from logging import Logger
from typing import Optional, Union, List, Tuple, cast

from ecosystem.commands import CloneRepoCommand
from ecosystem.models import (
    CommandExecutionSummary,
    RepositoryConfiguration,
    PythonRepositoryConfiguration,
    FilesTemplates,
)
from ecosystem.models.repository import Repository
from ecosystem.utils import QiskitEcosystemException
from ecosystem.utils import logger as ecosystem_logger
from ecosystem.utils.utils import set_actions_output


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

    def configure_repo(
        self,
        files: List[str],
        files_fault: List[str],
        ecosystem_deps: Optional[List[str]] = None,
    ):
        """Configuring the different templates:
            - tox.ini
            - .pylintrc
            - .coveragerc

        Args:
            files: list of files (tox.ini/.pylintrc/.coveragerc)
            files_fault: list of default name replacement
            ecosystem_deps: list of dependence

        No return
        """
        if len(files) != len(files_fault):
            raise ValueError(
                "The number of element in files aren't the same as in files_fault"
            )

        if self.repo_config is not None:
            repo_config = self.repo_config
        elif os.path.exists(f"{self.cloned_repo_directory}/ecosystem.json"):
            self.logger.info("Configuration file exists.")
            loaded_config = RepositoryConfiguration.load(
                f"{self.cloned_repo_directory}/ecosystem.json"
            )
            repo_config = cast(PythonRepositoryConfiguration, loaded_config)
        else:
            repo_config = PythonRepositoryConfiguration.default()

        # check for tox/.pylintrc/.coveragerc file
        for destination_file_name, renamed_file_name in zip(files, files_fault):
            if os.path.exists(f"{self.cloned_repo_directory}/{destination_file_name}"):
                self.logger.info("{destination_file_name} file exists.")
                os.rename(
                    f"{self.cloned_repo_directory}/{destination_file_name}",
                    f"{self.cloned_repo_directory}/{renamed_file_name}",
                )

            # render new tox/.pylintrc/.coveragerc file for tests
            with open(
                f"{self.cloned_repo_directory}/{destination_file_name}", "w"
            ) as param_file:
                if destination_file_name == FilesTemplates.TOX_FILE_NAME:
                    param_file.write(
                        repo_config.render_tox_file(ecosystem_deps=ecosystem_deps)
                    )
                elif destination_file_name == FilesTemplates.LINT_FILE_NAME:
                    param_file.write(repo_config.render_lint_file())
                elif destination_file_name == FilesTemplates.COV_FILE_NAME:
                    param_file.write(repo_config.render_cov_file())
                else:
                    raise ValueError(
                        "{destination_file_name} doesn't correspond to anything"
                    )

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
            for i in result[1]:
                warn_logs = CommandExecutionSummary.get_warning_logs(i)
                set_actions_output([("WARN", str(warn_logs))])
        except Exception as exception:  # pylint: disable=broad-except
            result = ("-", CommandExecutionSummary(1, [], summary=str(exception)))
            self.logger.error(exception)
        self.tear_down()
        return result
