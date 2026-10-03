# This code is part of Qiskit.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Generate the docs/assets/ fragments that the pages read with `read_raw`/`read_json`:
the classification tables, the badge table and the check up page.

This runs as a mkdocs `gen-files` script, so a documentation build always has fragments
that match the member files, with no separate command to remember. The writes are skipped
when the content has not changed, so a rebuild does not trigger the next one.

The summary page charts and the members badge are published rather than written: they are
fetched from the site by whoever renders them, and mkdocs only copies the files that were
in `docs/` when the build started, so a fragment written mid-build has to be registered
through `mkdocs_gen_files` to end up in the site at all.
"""

import mkdocs_gen_files

from ecosystem.cli.members import CliMembers
from ecosystem.docs.summary_charts import fragments

members = CliMembers()
members.update_docs_assets()

for name, text in fragments(members.dao.get_all()).items():
    with mkdocs_gen_files.open(f"assets/{name}", "w") as fragment:
        fragment.write(text)
