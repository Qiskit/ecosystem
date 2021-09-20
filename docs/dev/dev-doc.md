Dev docs
========

As entire repository is designed to be run through GitHub Actions,
we implemented ecosystem python package as runner of CLI commands
to be executed from steps in Actions. 

Entrypoint is ``manager.py`` file in the root of repository.

Example of commands:
```shell
python manager.py python_dev_tests https://github.com/IceKhan13/demo-implementation --python_version=py39
python manager.py python_stable_tests https://github.com/IceKhan13/demo-implementation --python_version=py39
```
or in general
```shell
python manager.py <NAME_OF_FUNCTION_IN_MANAGER_FILE> <POSITIONAL_ARGUMENT> [FLAGS]
```

#### Ecosystem workflows configuration

In order to talk control of execution workflow of tests in ecosystem
repository should have `qe_config.json` file in a root directory.

Structure of config file:
- dependencies_files: list[string] - files with package dependencies (ex: requirements.txt, packages.json)
- extra_dependencies: list[string] - names of additional packages to install before tests execution
- language: string - programming language for tests env. Only supported lang is Python at this moment.
- tests_command: list[string] - list of commands to execute tests

Example:
```json
{
    "dependencies_files": [
        "requirements.txt",
        "requirements-dev.txt"
    ],
    "extra_dependencies": [
        "pytest"
    ],
    "language": "python",
    "tests_command": [
        "pytest -p no:warnings --pyargs test"
    ]
}
```
