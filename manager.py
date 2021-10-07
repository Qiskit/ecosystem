"""Entrypoint for CLI

Available commands:

1. Run tests within repository.
```shell
python manager.py standard_tests https://github.com/<ACCOUNT>/<REPOSITORY_NAME> --tox_python=<py36,py37,py38,py39>
```

2. Run tests against stable version of Qiskit.
```shell
python manager.py stable_compatibility_tests https://github.com/<ACCOUNT>/<REPOSITORY_NAME> --tox_python=<py36,py37,py38,py39>
```

3. Run tests against dev version of Qiskit.
```shell
python manager.py dev_compatibility_tests https://github.com/<ACCOUNT>/<REPOSITORY_NAME> --tox_python=<py36,py37,py38,py39>
```

4. Get parse issue.
```shell
python manager.py parser_issue --body="${{ github.event.issue.body }}"
```
"""
import fire

from ecosystem import Manager


if __name__ == "__main__":
    fire.Fire(Manager)
