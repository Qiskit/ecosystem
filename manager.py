// This code is part of Qiskit.
//
// (C) Copyright IBM 2026
//
// This code is licensed under the Apache License, Version 2.0. You may
// obtain a copy of this license in the LICENSE.txt file in the root directory
// of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
//
// Any modifications or derivative works of this code must retain this
// copyright notice, and modified files need to carry a notice indicating
// that they have been altered from the originals.


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
