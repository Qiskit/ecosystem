Dev docs
========

As entire repository is designed to be run through GitHub Actions,
we implemented ecosystem python package as runner of command line commands
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
