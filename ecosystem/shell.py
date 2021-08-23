"""Shell commands and utils."""
import os
import shutil
import subprocess
from typing import Optional, List, Dict
import setuptools

from jinja2 import Template

from ecosystem.entities import CommandExecutionSummary


def _execute_command(command: List[str],
                     cwd: Optional[str] = None) -> CommandExecutionSummary:
    """Executes specified command as subprocess in a directory."""
    with subprocess.Popen(command,
                          stdout=subprocess.PIPE,
                          cwd=cwd) as process:
        logs = []
        while True:
            output = str(process.stdout.readline())
            print(output.strip())
            logs.append(output.strip())
            return_code = process.poll()
            if return_code is not None:
                print('RETURN CODE', return_code)
                for output in process.stdout.readlines():
                    logs.append(str(output).strip())

                return CommandExecutionSummary(code=return_code,
                                               logs=logs)


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
                            cwd=directory)


def _cleanup(directory: Optional[str] = None):
    """Removes temp directory."""
    if directory and os.path.exists(directory):
        shutil.rmtree(directory)


def basic_tests(repo: str, resources_dir: str,
                tox_python: str) -> Dict[str, CommandExecutionSummary]:
    """Run all tests for repository."""
    name = repo.split("/")[-1]

    directory = "{}/cloned_repos_directory".format(resources_dir)
    cloned_repo_directory = f"{directory}/{name}"

    _cleanup(directory)
    os.makedirs(directory)

    # execute steps: clone repo and run tests
    clone_res = _clone_repo(repo, directory=directory)
    tox_exists_res = _check_tox_ini(cloned_repo_directory)
    tests_res = _run_tox(cloned_repo_directory, tox_python)
    # TODO: figure out why linter is failing with `File contains utf-8 header` # pylint: disable=fixme
    # _run_tox(cloned_repo_directory, "lint", file=file)

    _cleanup(cloned_repo_directory)

    return {
        "repo clone": clone_res,
        "check for tox file": tox_exists_res,
        "tests result": tests_res
    }


def stable_tests(repo: str,
                 resources_dir: str,
                 tox_python: str,
                 template: Template) -> Dict[str, CommandExecutionSummary]:
    """Runs tests against stable version of Qiskit."""
    name = repo.split("/")[-1]

    directory = "{}/cloned_repos_directory".format(resources_dir)
    cloned_repo_directory = f"{directory}/{name}"

    _cleanup(directory)
    os.makedirs(directory)
    # execute steps: clone repo and run tests
    clone_res = _clone_repo(repo, directory=directory)
    tox_exists_res = _check_tox_ini(cloned_repo_directory)

    res = {
        "repo clone": clone_res,
        "check for tox file": tox_exists_res
    }

    if clone_res.ok and tox_exists_res:
        # rename old tox file
        os.rename(f"{cloned_repo_directory}/tox.ini",
                  f"{cloned_repo_directory}/default_tox.ini")

        # create new tox file for stable tests
        packages = setuptools.find_packages(cloned_repo_directory)
        with open(f"{cloned_repo_directory}/tox.ini", "w") as tox_file:
            tox_file.write(template.render(packages=packages))

        res["stable tests results"] = _run_tox(cloned_repo_directory, tox_python)

    _cleanup(directory)

    return res
