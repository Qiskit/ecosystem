"""Entrypoint for CLI

Available commands:

1. Run tests within repository.
```shell
python manager.py tests python_standard_tests https://github.com/<ACCOUNT>/<REPOSITORY_NAME> --tox_python=<py36,py37,py38,py39>
```

2. Run tests against stable version of Qiskit.
```shell
python manager.py tests python_stable_tests https://github.com/<ACCOUNT>/<REPOSITORY_NAME> --tox_python=<py36,py37,py38,py39>
```

3. Run tests against dev version of Qiskit.
```shell
python manager.py tests python_dev_tests https://github.com/<ACCOUNT>/<REPOSITORY_NAME> --tox_python=<py36,py37,py38,py39>
```

4. Get parse issue.
```shell
python manager.py ci parser_issue --body="${{ github.event.issue.body }}"
```

5. Add repo to jsondb.
```shell
python manager.py members add_repo_2db --repo_link="https://github.com/<ACCOUNT>/<REPOSITORY_NAME>" --repo_author="<ACCOUNT>" ...
```

6. Recompile members.
```shell
python manager.py members recompile"
```

7. Build website.
```shell
python manager.py website build_website"
```
"""
import fire

from ecosystem.cli import CliMembers, CliWebsite, CliCI, CliTests


if __name__ == "__main__":
    fire.Fire(
        {
            "members": CliMembers,
            "tests": CliTests,
            "website": CliWebsite,
            "ci": CliCI,
        }
    )
