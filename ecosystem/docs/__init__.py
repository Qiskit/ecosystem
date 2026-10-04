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

from slugify import slugify


def anchor(name: str) -> str:
    """Anchor of the section about a classification value in its documentation page.

    The classification pages (maturity, categories, labels, interfaces) give every section
    an explicit heading id, and the cards in the project pages link to them, so both sides
    have to build the same string from the same name. `+` becomes `p` because `slugify`
    drops it, which would leave `C` and `C++` sharing a single `#c` anchor.
    """
    return slugify(name, replacements=[["+", "p"]])


def cell(text) -> str:
    """A value that is safe to use inside a Markdown table cell"""
    return str(text).replace("|", "\\|").replace("\n", " ")


def tooltip(text) -> str:
    """A value that is safe to use inside a Markdown attr_list title="..." """
    return cell(text).replace('"', "&quot;")


def plural(projects, word="project") -> str:
    """How many projects there are, as `1 project` or `2 projects`"""
    return f"{len(projects)} {word}{'' if len(projects) == 1 else 's'}"


def project_link(project) -> str:
    """A project, linked to its page. The fragments are read into pages that live in docs/,
    so the link is relative to that directory and not to the fragment."""
    return f"[{cell(project.name)}](p/{project.short_uuid}.md)"


def write_if_changed(path, text) -> bool:
    """Writes `text` to `path`, but only when that is not already its content.

    The docs/assets/ fragments are regenerated on every documentation build, including the
    rebuilds of `properdocs serve`. Rewriting a file under docs/ is what the file watcher reacts
    to, so leaving an unchanged file alone is what keeps one build from triggering the next.
    Returns whether the file was written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() == text:
        return False
    path.write_text(text)
    return True


def markdown_table(columns, rows) -> list:
    """A table as lines, leaving out every column that no row has something in.

    `columns` are (header, alignment) pairs and `rows` the cells, already rendered: what a
    cell holds depends on the table, but whether a column is worth a header does not.
    """
    if not rows:
        return []
    keep = [index for index, _ in enumerate(columns) if any(row[index] for row in rows)]
    return [
        "| " + " | ".join(columns[index][0] for index in keep) + " |",
        "| " + " | ".join(columns[index][1] for index in keep) + " |",
    ] + ["| " + " | ".join(row[index] for index in keep) + " |" for row in rows]


def command_block(command, language="bash") -> list:
    """A command to run, as a fenced block with the copy button the theme adds to one.

    Inline code renders a command a reader has to select by hand. `content.code.copy` (see
    `theme.features` in properdocs.yml) gives a fenced block the same copy button the badge
    snippet has, and copying it is the only thing anybody does with a command.
    """
    return [f"```{language}", command, "```"]
