"""Entrypoint for CLI

Available commands:

1. Get parse issue.

   ```shell
   python manager.py ci parser_issue --body="${{ github.event.issue.body }}"
   ```

2. Add repo to tomldb.
   ```shell
   python manager.py members add_repo_2db --repo_link="https://github.com/<ACCOUNT>/<REPOSITORY_NAME>" --repo_author="<ACCOUNT>" ...
   ```

3. Build website.
   ```shell
   python manager.py website build_website"
   ```
"""

from ecosystem import main

if __name__ == "__main__":
    main()
