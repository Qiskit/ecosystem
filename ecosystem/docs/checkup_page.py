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

"""
The docs/assets/ fragments that https://qiskit.github.io/ecosystem/checkups/ reads,
generated from resources/checks.toml and the member files so they cannot drift from them.
"""

import json
from pathlib import Path

from slugify import slugify

from ecosystem.docs import write_if_changed


class CheckupAssets:  # pylint: disable=too-many-public-methods
    """The generated parts of the Check ups page.

    Most of the methods are small formatting helpers for one column or one block of the
    page, kept separate so each piece of the markup has an obvious home.

    `checkup.json` is its summary table and `checkup.md` its body, one section per check up
    with the projects that are failing it. `checkup-importance.md` and
    `checkup-categories.md` are the reference tables that the overview page reads.
    """

    def __init__(self, checks_toml, projects, assets_dir):
        self.checks_toml = checks_toml
        self.checkups = dict(sorted(checks_toml.checkups.items()))
        self.assets_dir = Path(assets_dir)
        self.pending, self.explained = self._projects_per_checkup(projects)

    def write_all(self):
        """Writes the four fragments"""
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.write("checkup.json", json.dumps(self.summary_rows()), newline=False)
        self.write("checkup.md", "\n".join(self.sections()))
        self.write("checkup-importance.md", "\n".join(self.importance_table()))
        self.write("checkup-categories.md", "\n".join(self.categories_table()))

    def write(self, filename, text, newline=True):
        """Writes a fragment. See `ecosystem.docs.write_if_changed`"""
        return write_if_changed(
            Path(self.assets_dir, filename), f"{text}\n" if newline else text
        )

    def _projects_per_checkup(self, projects):
        """Two dicts checkup_id -> [Member], for the projects that have the check up
        recorded: the ones it is pending on, and the ones with a valid explanation for it.
        """
        pending = {id_: [] for id_ in self.checkups}
        explained = {id_: [] for id_ in self.checkups}
        for project in projects:
            for checkup_id, checkup in project.checks.items():
                where = explained if checkup.xfail_applies else pending
                # setdefault: a member file may name a check up checks.toml no longer has
                where.setdefault(checkup_id, []).append(project)
        return pending, explained

    # ---------------------------------------------------------------- small helpers

    @staticmethod
    def cell(text):
        """A string that is safe to use inside a Markdown table cell"""
        return str(text).replace("|", "\\|").replace("\n", " ")

    @classmethod
    def tooltip(cls, text):
        """A string that is safe to use inside a Markdown attr_list title="..." """
        return cls.cell(text).replace('"', "&quot;")

    @classmethod
    def plural(cls, projects, word="project"):
        """How many projects there are, as `1 project` or `2 projects`"""
        return f"{len(projects)} {word}{'' if len(projects) == 1 else 's'}"

    @classmethod
    def link(cls, project):
        """A project, linked to its page"""
        return f"[{cls.cell(project.name)}](p/{project.short_uuid}.md)"

    @staticmethod
    def discussion_link(checkup):
        """The `discussion` of a check up as a link, when it has one"""
        return f"[discussion]({checkup.discussion})" if checkup.discussion else ""

    @staticmethod
    def cure_period_str(days):
        """A `cure_period_in_days` value as a table cell"""
        if days is None:
            return "not defined"
        if days < 0:
            return "no deadline"
        return f"{days} days"

    def cure_period_of(self, checkup_id):
        """The cure period of a check up, as a table cell"""
        return self.cure_period_str(self.checks_toml.cure_period(checkup_id))

    def icon_of(self, importance):
        """The importance icon of a check up, as an inline element with a tooltip"""
        level = self.checks_toml.importance(importance) if importance else {}
        if not level.get("icon"):
            return ""
        return (
            f':{level["icon"]}:'
            f'{{ title="{self.tooltip(level.get("description", ""))}" }}'
        )

    @staticmethod
    def days_left(project, checkup):
        """The cure period left on a check up, as a table cell. There is nothing to count for
        an alumni project: its cure period is what retired it in the first place."""
        if project.status == "Alumni":
            return "&mdash;"
        days = checkup.days_left_in_cure_period
        if days is None:
            return "&infin;" if checkup.cure_period_is_infinite else "&mdash;"
        return str(days) if days >= 0 else "overdue"

    @staticmethod
    def expires_in(checkup):
        """When the explanation for a check up stops applying, as a table cell"""
        days = checkup.days_until_xfailed_expires
        return "never" if days is None else f"{days} days"

    # ---------------------------------------------------------------- the fragments

    def summary_rows(self):
        """The rows of the summary table at the top of the page"""
        return [
            {
                "Check up": f"[`[{id_}]` {self.cell(checkup['title'])}](#{id_})",
                "Applies to": self.cell(checkup.get("applies_to", "all")),
                "Category": self.cell(checkup["category"]),
                "Importance": f"{self.icon_of(checkup.get('importance'))} "
                f"{self.cell(checkup.get('importance'))}",
                "Cure period": self.cure_period_of(id_),
                "Failing": len([p for p in self.pending[id_] if p.status != "Alumni"]),
            }
            for id_, checkup in self.checkups.items()
        ]

    def sections(self):
        """One section per check up, with the projects that are failing it"""
        lines = []
        for id_, checkup in self.checkups.items():
            lines += self.section_header(id_, checkup)
            lines += self.pending_block(id_)
            lines += ["", ""]
            lines += self.explained_block(id_)
        # every mention of a category on the page gets its description as a tooltip
        lines += [
            f'*[{category["name"]}]: {category["description"]}'
            for category in self.checks_toml.categories
        ]
        return lines + [""]

    def section_header(self, id_, checkup):
        """The heading of a check up section, what it is about, and how it is checked"""
        importance = checkup.get("importance")
        lines = [
            f'## `[{id_}]` {self.cell(checkup["title"])} {{ #{id_} }}',
            "",
            f"{self.icon_of(importance)} **{self.cell(importance)}** "
            f"&middot; {self.cell(checkup['category'])} "
            f"&middot; applies to {self.cell(checkup.get('applies_to', 'all'))} "
            f"&middot; cure period: {self.cure_period_of(id_)}",
            "",
            checkup["description"],
            "",
        ]
        checker = checkup.get("checker")
        if not checker:
            return lines + [
                "This check up is not a test: it is raised by hand, and tracked in the "
                "issue that the member file points to.",
                "",
            ]
        if "::" not in checker:
            return lines + [f"Checked by `{checker}`.", ""]
        return lines + [
            f"Checked by [`{checker}`](https://github.com/Qiskit/ecosystem/blob/main/"
            f"ecosystem/validation/{checker.split('::')[0]}).",
            "",
        ]

    def pending_block(self, id_):
        """The projects a check up is pending on, the alumni among them listed apart"""
        alumni = [p for p in self.pending[id_] if p.status == "Alumni"]
        members = [p for p in self.pending[id_] if p.status != "Alumni"]
        if not members:
            if not alumni:
                return ["**No project is failing this check up**"]
            return [
                "**No current member is failing this check up**"
            ] + self.alumni_list(alumni)
        return self.project_table(
            f"There {'is' if len(members) == 1 else 'are'} {self.plural(members)} "
            "failing this check up",
            [
                (
                    project,
                    [
                        self.days_left(project, project.checks[id_]),
                        self.discussion_link(project.checks[id_]),
                    ],
                )
                for project in members
            ],
            [("Days left in the cure period", "---:"), ("Discussion", ":---:")],
            nested=self.alumni_list(alumni, indent="    ") if alumni else (),
        )

    def explained_block(self, id_):
        """The projects with a valid explanation for a check up"""
        if not self.explained[id_]:
            return []
        return self.project_table(
            f"{self.plural(self.explained[id_])} with an explanation for this check up",
            [
                (
                    project,
                    [
                        self.cell(project.checks[id_].xfailed),
                        self.expires_in(project.checks[id_]),
                        self.discussion_link(project.checks[id_]),
                    ],
                )
                for project in self.explained[id_]
            ],
            [
                ("Explanation", "---"),
                ("Explanation expires in", "---:"),
                ("Discussion", ":---:"),
            ],
        ) + ["", ""]

    def project_table(self, summary, rows, columns, nested=()):
        """A collapsible table of projects. `columns` are the (header, alignment) pairs that
        follow the fixed Project, Maturity and Status ones, and each row is a
        (project, [cell per column]) pair. A column with nothing in it is left out, so a
        table only carries the explanation or the discussion when there is one.
        `nested` goes inside the collapsible, after the table."""
        keep = [i for i in range(len(columns)) if any(cells[i] for _, cells in rows)]
        header = "    | Project | Maturity | Status"
        divider = "    | --- | :---: | :---:"
        for i in keep:
            header += f" | {columns[i][0]}"
            divider += f" | {columns[i][1]}"
        lines = [f'??? note "{summary}"', "", f"{header} |", f"{divider} |"]
        for project, cells in rows:
            row = (
                f"    | {self.link(project)}"
                f" | {self.cell(project.maturity or '')}"
                f" | {self.cell(project.status or 'Member')}"
            )
            for i in keep:
                row += f" | {cells[i]}"
            lines.append(f"{row} |")
        return lines + list(nested)

    def alumni_list(self, projects, indent=""):
        """A collapsible list of the alumni that were failing a check up. They are kept out
        of the table: there is no cure period left to report on a project that the check up
        already retired."""
        return [
            "",
            f'{indent}??? info "{self.plural(projects, "Alumni project")} '
            f'also failed this check up"',
            "",
        ] + [f"{indent}    - {self.link(project)}" for project in projects]

    def importance_table(self):
        """The importance levels and the cure period each one defaults to"""
        lines = [
            "| importance | description | default cure period |",
            "| :---: | --- | :---: |",
        ]
        for importance in self.checks_toml.importances:
            lines.append(
                f'| :{importance.get("icon", "")}: '
                f'<span id="{slugify(importance["name"])}">'
                f'**{self.cell(importance["name"])}**</span>'
                f' | {self.cell(importance["description"])}'
                f' | {self.cure_period_str(importance.get("cure_period_in_days"))} |'
            )
        return lines

    def categories_table(self):
        """The check up categories"""
        lines = ["| category | description |", "| :---: | --- |"]
        for category in self.checks_toml.categories:
            lines.append(
                f'| <span id="{slugify(category["name"])}">'
                f'**{self.cell(category["name"])}**</span>'
                f' | {self.cell(category["description"])} |'
            )
        return lines
