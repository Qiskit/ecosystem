"""Command execution."""
import os
import shutil
import subprocess
from typing import Optional, List

from ecosystem.models import CommandExecutionSummary
from ecosystem.utils import logger


def _execute_command(command: List[str],
                     cwd: Optional[str] = None,
                     name: Optional[str] = None) -> CommandExecutionSummary:
    """Executes specified command as subprocess in a directory."""
    with subprocess.Popen(command,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          cwd=cwd) as process:
        logs = []
        while True:
            output = str(process.stdout.readline())
            logger.info(output.strip())
            logs.append(output.strip())
            return_code = process.poll()
            if return_code is not None:
                logger.info('RETURN CODE: %s}', return_code)
                for output in process.stdout.readlines():
                    logger.info(str(output).strip())
                    logs.append(str(output).strip())

                return CommandExecutionSummary(code=return_code,
                                               logs=logs,
                                               name=name)


def _clone_repo(repo: str, directory: str) -> CommandExecutionSummary:
    """Clones repo in directory."""
    return _execute_command(["git", "-C", directory, "clone", repo])


def _check_tox_ini(directory: str) -> CommandExecutionSummary:
    """Checks for tox file existance."""
    if not os.path.isfile("{}/tox.ini".format(directory)):
        return CommandExecutionSummary(code=1,
                                       logs=[],
                                       summary="No tox.ini file in project.")
    return CommandExecutionSummary.empty()


def _run_tox(directory: str, env: str) -> CommandExecutionSummary:
    """Run tox test."""
    return _execute_command(["tox", "-e{}".format(env),
                             "--workdir", directory],
                            cwd=directory,
                            name="tests")


def _run_lint(directory: str) -> CommandExecutionSummary:
    """Run lint test."""
    return _execute_command(["tox", "-elint",
                             "--workdir", directory],
                            cwd=directory,
                            name="styles_check")


def _cleanup(directory: Optional[str] = None):
    """Removes temp directory."""
    if directory and os.path.exists(directory):
        shutil.rmtree(directory)
