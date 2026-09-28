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

"""Test-wide safety net: no test may write the repository's own member files.

Tests are expected to point their `DAO` at a temporary directory, and they all do.
But nothing enforced it, and a `DAO` is easy to build against the real one by
accident: `CliMembers(root_path=<repo root>)` does exactly that in its `__init__`
(see `tests/test_cli.py`), and only the `.dao` attribute is replaced afterwards.
`TomlStorage.write` rewrites *every* member file when no `name_id` is set, and
`refresh_files` deletes the directory first, so a slip is a large, silent diff in
`resources/members/` rather than a failing test.

Turning that into an immediate failure costs one patch, so it is patched here.
"""

from pathlib import Path

from ecosystem.dao import TomlStorage

REAL_MEMBERS_DIR = (Path(__file__).parent.parent / "resources" / "members").resolve()

_write = TomlStorage.write
_refresh_files = TomlStorage.refresh_files


def _is_real(storage):
    try:
        return Path(storage.toml_dir).resolve() == REAL_MEMBERS_DIR
    except OSError:  # pragma: no cover - an unresolvable path is not the real one
        return False


def _guard(storage, what):
    if _is_real(storage):
        raise AssertionError(
            f"a test called TomlStorage.{what}() on the repository's own member files "
            f"({REAL_MEMBERS_DIR}). Point the DAO at a temporary directory instead."
        )


def write(self, data):
    """`TomlStorage.write`, refusing to touch the real member files."""
    _guard(self, "write")
    return _write(self, data)


def refresh_files(self):
    """`TomlStorage.refresh_files`, refusing to touch the real member files."""
    _guard(self, "refresh_files")
    return _refresh_files(self)


TomlStorage.write = write
TomlStorage.refresh_files = refresh_files
