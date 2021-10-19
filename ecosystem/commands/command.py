"""Command execution."""
import os
import subprocess
from abc import abstractmethod
from typing import Optional, List

from ecosystem.models import CommandExecutionSummary
from ecosystem.utils import logger


# pylint: disable=arguments-differ
class Command:
    """General for executable shell commands."""

    def __init__(self, name: Optional[str] = None, cwd: Optional[str] = None):
        """General class for executable shell commands.

        Args:
            name: name for command
            cwd: directory where to execute command
        """
        self.name = name or "unnamed_command"
        self.cwd = cwd

    @classmethod
    def subprocess_execute(
        cls, command: List[str], name: Optional[str] = None, cwd: Optional[str] = None
    ):
        """Executes specified command as subprocess in a directory."""
        with subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd
        ) as process:
            logs = []
            while True:
                output = str(process.stdout.readline().decode())
                logger.info(output.strip())
                logs.append(output.strip())
                return_code = process.poll()
                if return_code is not None:
                    logger.info("[RETURN CODE]: %s", return_code)
                    for output in process.stdout.readlines():
                        logger.info(str(output).strip())
                        logs.append(str(output).strip())

                    return CommandExecutionSummary(
                        code=return_code, logs=logs, name=name
                    )

    @classmethod
    @abstractmethod
    def execute(cls, **kwargs) -> CommandExecutionSummary:
        """Executes command."""


class ShellCommand(Command):
    """Arbitrary shell command."""

    @classmethod
    def execute(
        cls, command: List[str], directory: str, **kwargs
    ) -> CommandExecutionSummary:
        return cls.subprocess_execute(
            command=command, cwd=directory, name=" ".join(command)
        )


class CloneRepoCommand(Command):
    """Clone repo command."""

    @classmethod
    def execute(cls, repo: str, directory: str, **kwargs) -> CommandExecutionSummary:
        return cls.subprocess_execute(
            ["git", "-C", directory, "clone", repo], name="Clone repo"
        )


class RunToxCommand(Command):
    """Running tox."""

    @classmethod
    def execute(cls, directory: str, env: str, **kwargs) -> CommandExecutionSummary:
        return cls.subprocess_execute(
            ["tox", "-e{}".format(env), "--workdir", directory],
            cwd=directory,
            name="Tests",
        )


class FileExistenceCheckCommand(Command):
    """Check for file existence."""

    @classmethod
    def execute(cls, file: str, directory: str, **kwargs) -> CommandExecutionSummary:
        if not os.path.isfile("{}/{}".format(directory, file)):
            return CommandExecutionSummary(
                code=1, logs=[], summary="No {} file in project.".format(file)
            )
        return CommandExecutionSummary.empty()
