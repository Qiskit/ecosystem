"""Entrypoint for CLI

Available commands:

1. Get parse issue.
```shell
python manager.py parser_issue --body="${{ github.event.issue.body }}"
```

2. Add repo to tomldb.
```shell
python manager.py add_repo_2db --repo_link="https://github.com/<ACCOUNT>/<REPOSITORY_NAME>" --repo_author="<ACCOUNT>" ...
```
"""
import fire

from ecosystem import Manager


if __name__ == "__main__":
    fire.Fire(Manager)
