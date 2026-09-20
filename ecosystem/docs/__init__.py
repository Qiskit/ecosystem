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

"""Ecosystem documentation module."""

from pathlib import Path


def write_if_changed(path, text) -> bool:
    """Writes `text` to `path`, but only when that is not already its content.

    The docs/assets/ fragments are regenerated on every documentation build, including the
    rebuilds of `mkdocs serve`. Rewriting a file under docs/ is what the file watcher reacts
    to, so leaving an unchanged file alone is what keeps one build from triggering the next.
    Returns whether the file was written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() == text:
        return False
    path.write_text(text)
    return True
