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
"""

from ecosystem.cli.members import CliMembers

CliMembers().update_docs_assets()
