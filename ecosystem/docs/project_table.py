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

"""Collapsible tables of projects for the docs/assets/ fragments of the classification
pages, in the style of the tables of the check up page (`ecosystem.docs.checkup_page`).

A section of a classification page is about one value, so the table does not repeat it:
each page picks the columns that add something next to the value the section is about.
"""

from dataclasses import dataclass
from typing import Callable

from ecosystem.docs import cell, plural, project_link


@dataclass(frozen=True)
class Column:
    """One column of a project table: its header, its alignment, and how to fill a cell"""

    header: str
    alignment: str
    value: Callable

    def cell(self, project) -> str:
        """The cell of this column for a project"""
        return cell(self.value(project) or "")


def code_list(values) -> str:
    """Classification values of a project, as inline code in a single cell"""
    return ", ".join(f"`{cell(value)}`" for value in values or [])


def checkup_list(project) -> str:
    """The check ups recorded on a project, linked to their section in the check up page.
    The ones with a valid explanation are left out: they are not what puts a project under
    revision."""
    return " ".join(
        f"[`[{checkup_id}]`](checkups.md#{checkup_id})"
        for checkup_id, checkup in sorted(project.checks.items())
        if not checkup.xfail_applies
    )


MATURITY = Column("Maturity", ":---:", lambda p: p.maturity)
STATUS = Column("Status", ":---:", lambda p: p.status or "Member")
CATEGORY = Column("Category", "---", lambda p: p.category)
LABELS = Column("Labels", "---", lambda p: code_list(p.labels))
INTERFACES = Column("Interfaces", "---", lambda p: code_list(p.interfaces))
LAST_COMMIT = Column(
    "Last commit", ":---:", lambda p: getattr(p.github, "last_commit", None)
)
CHECKUPS = Column("Pending check ups", "---", checkup_list)
GITHUB_ORG = Column(
    "GitHub organization",
    "---",
    lambda p: (
        f"[{cell(p.github.owner)}](https://github.com/{p.github.owner})"
        if getattr(p.github, "owner", None)
        else None
    ),
)


def other_interfaces(name):
    """The interfaces of a project other than `name`, for the section about `name`"""
    return Column(
        "Other interfaces",
        "---",
        lambda p: code_list([i for i in p.interfaces or [] if i != name]),
    )


def classification_table(projects, columns, summary=None, open_by_default=False):
    """A collapsible table with one row per project, as a list of lines.

    `columns` are the ones that follow the Project column. A column that is empty for every
    project is left out, so a table only carries what it has something to say about.
    """
    summary = summary or f"There are {plural(projects)} with this classification"
    header = "    | Project"
    divider = "    | ---"
    keep = [column for column in columns if any(column.cell(p) for p in projects)]
    for column in keep:
        header += f" | {column.header}"
        divider += f" | {column.alignment}"
    lines = [
        f'???{"+" if open_by_default else ""} note "{summary}"',
        "",
        f"{header} |",
        f"{divider} |",
    ]
    for project in projects:
        row = f"    | {project_link(project)}"
        for column in keep:
            row += f" | {column.cell(project)}"
        lines.append(f"{row} |")
    return lines


def classification_columns(classification, name):
    """The columns of the table in the section about `name`, in the page of
    `classification`. The classification of the section itself is not a column: every row
    would carry the same value."""
    columns = {
        "status": [MATURITY, CATEGORY, LAST_COMMIT],
        "maturity": [STATUS, CATEGORY, LABELS, LAST_COMMIT],
        "category": [MATURITY, STATUS, LABELS, LAST_COMMIT],
        "labels": [MATURITY, STATUS, CATEGORY, LAST_COMMIT],
        "interfaces": [MATURITY, STATUS, CATEGORY, other_interfaces(name)],
    }
    return columns.get(classification, [MATURITY, STATUS, CATEGORY, LAST_COMMIT])
