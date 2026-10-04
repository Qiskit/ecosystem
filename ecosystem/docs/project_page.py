# This code is part of Qiskit.
#
# (C) Copyright IBM 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Pages inhttps://qiskit.github.io/ecosystem/p/<short uuid>
"""

import mkdocs_gen_files

from ecosystem.classifications import ClassificationsToml
from ecosystem.docs import cell, markdown_table, tooltip
from ecosystem.docs.card import (
    ProjectSummaryCard,
    URLsCard,
    compatibility_mark,
    pip_install_target,
)
from ecosystem.docs.checkup_page import CheckupAssets


class ProjectPage:  # pylint: disable=redefined-outer-name
    """represents a markdown file in docs/p/"""

    classifications = ClassificationsToml()

    def __init__(self, project, filename):
        """each of the files in docs/p/*.md"""
        self.project = project
        self.filename = filename

    def generate_all_lines(self):
        """Returns all the docs/p/<uuid>.md lines"""
        lines = []
        lines += self.front_matter()
        lines += self.title() + [""]
        lines += self.description() + [""]
        lines += self.general_summary()
        lines += self.badge()
        lines += self.checkups()
        lines += self.packages()
        lines += self.qiskit_requirements()
        return lines

    def general_summary(self):
        """Summary section"""
        return (
            ['<div class="grid cards" markdown>', ""]
            + self.classification_card()
            + self.urls_card()
            + ["</div>"]
        )

    def packages(self):
        """Packages section: one table per kind of registry, in the order they are stored.

        Qiskit compatibility is not here. It is the same four columns wherever the
        constraint was read from, so the `Qiskit requirements` table below collects it for
        the whole project instead of repeating it in every row of every table.
        """
        tables = (
            self.pypi_table()
            + self.crates_table()
            + self.cargo_table()
            + self.pip_source_table()
            + self.julia_table()
            + self.other_registries_table()
        )
        if not tables:
            return []
        return ["\n---\n### :material-package-variant: Packages\n"] + tables

    def pypi_table(self):
        """The distributions published to PyPI, each linked to its own page"""
        packages = self.project.pypi
        rows = [
            [
                f"[`{cell(package.package_name)}`](../pypi/{package.package_name}.md)",
                self._release_cell(
                    package.version, package.url, package.last_release_date
                ),
                self._count_cell(package.last_month_downloads),
                self._count_cell(package.last_180_days_downloads),
            ]
            for package in packages
        ]
        columns = [
            ("PyPI package", "---"),
            ("Release", ":---:"),
            ("Last month", "---:"),
            ("Last 180 days", "---:"),
        ]
        return self._table(columns, rows)

    def crates_table(self):
        """The crates published to crates.io.

        No Qiskit column, and no `Qiskit requirements` row either: Qiskit publishes no crate,
        so there is nothing on that registry for a crate to depend on.
        """
        rows = [
            [
                self._link_cell(
                    f"`{cell(crate.package_name)}`",
                    f"../crates/{crate.package_name}.md",
                ),
                self._release_cell(
                    crate.version,
                    f"{crate.url}/{crate.version}" if crate.version else None,
                    crate.last_release_date,
                ),
                cell(crate.rust_version) if crate.rust_version else "",
                cell(crate.edition) if crate.edition else "",
                self._count_cell(crate.total_downloads),
                self._count_cell(crate.last_90_days_downloads),
            ]
            for crate in self.project.crates
        ]
        columns = [
            ("crates.io crate", "---"),
            ("Release", ":---:"),
            ("Rust", ":---:"),
            ("Edition", ":---:"),
            ("Total downloads", "---:"),
            ("Last 90 days", "---:"),
        ]
        return self._table(columns, rows)

    def cargo_table(self):
        """The crates a repository declares without publishing them.

        `cargo add` is a tooltip rather than a column, as the `pip install` of the table
        below is: it is the longest value in the row and the shortest thing to say about
        the crate.
        """
        github = self.project.github
        owner = getattr(github, "owner", None)
        repo = getattr(github, "repo", None)
        rows = []
        for crate in self.project.cargo:
            target = (
                f"cargo add --git https://github.com/{owner}/{repo} "
                f"{crate.package_name}"
                if owner and repo
                else None
            )
            manifest = (
                f"[`{cell(crate.manifest_path)}`](https://github.com/{owner}/{repo}"
                f"/blob/HEAD/{crate.manifest_path})"
                if owner and repo
                else f"`{cell(crate.manifest_path)}`"
            )
            rows.append(
                [
                    self._link_cell(
                        f"`{cell(crate.package_name)}`",
                        f"../cargo-source/{crate.package_name}.md",
                        target,
                    ),
                    cell(crate.version) if crate.version else "",
                    cell(crate.rust_version) if crate.rust_version else "",
                    cell(crate.edition) if crate.edition else "",
                    manifest,
                ]
            )
        columns = [
            ("cargo-installable repo", "---"),
            ("Version", ":---:"),
            ("Rust", ":---:"),
            ("Edition", ":---:"),
            ("Declared in", "---"),
        ]
        return self._table(columns, rows)

    def pip_source_table(self):
        """The distributions a repository declares without publishing them anywhere.

        `pip install` is a tooltip rather than a column: it is the longest value in the
        table and it says nothing a reader cannot already see in the other columns.
        """
        github = self.project.github
        rows = []
        for package in self.project.python:
            target = pip_install_target(
                getattr(github, "owner", None),
                getattr(github, "repo", None),
                package.path,
            )
            rows.append(
                [
                    self._link_cell(
                        f"`{cell(package.package_name)}`",
                        f"../pip-source/{package.package_name}.md",
                        f"pip install {target}" if target else None,
                    ),
                    self._deferred_cell(package.version, package.deferred, "version"),
                    self._deferred_cell(
                        package.requires_python, package.deferred, "python_requires"
                    ),
                    ", ".join(
                        f"`{cell(manifest)}`" for manifest in package.source or []
                    ),
                ]
            )
        columns = [
            ("pip-installable repo", "---"),
            ("Version", ":---:"),
            ("Requires Python", ":---:"),
            ("Declared in", "---"),
        ]
        return self._table(columns, rows)

    def julia_table(self):
        """The packages registered in a Julia registry.

        A package nothing was fetched for keeps saying so in as many words: unlike the
        other registries, the row is only there because the registry was asked.
        """
        rows = [
            [
                f"`{cell(package.package_name)}`",
                self._release_cell(
                    package.version,
                    "https://juliahub.com/ui/Packages/"
                    f"{package.registry}/{package.package_name}",
                    package.release_date,
                )
                or "N/A",
                self._count_cell(package.estimated_unique_users),
            ]
            for package in self.project.julia
        ]
        columns = [
            ("Julia package", "---"),
            ("Release", ":---:"),
            ("Estimated users", "---:"),
        ]
        return self._table(columns, rows)

    def other_registries_table(self):
        """The registries with no section of their own, recognized by their host.

        A declared URL that a section reads is left out: the table above already says what
        was read from it. The URLs used to be deleted from `packages` once read, which is
        what this filter replaces.
        """
        rows = [
            self._registry_row(package)
            for package in self.project.packages or []
            if not self.project.declares_a_section(package)
        ]
        columns = [("Registry", "---"), ("Package", "---")]
        return self._table(columns, rows)

    @staticmethod
    def _registry_row(package):
        """A package URL as a row: the registry it is in, and what it is called there.

        The name is in a different part of the URL in every registry, so a host that is not
        recognized puts the link itself in the Registry column and names nothing.
        """
        if "visualstudio.com" in package.hostname:
            return [
                ":material-microsoft-visual-studio: Visual Studio Marketplace",
                f"[{cell(package.query.split('=')[1])}]({package})",
            ]
        if "ocaml.org" in package.hostname:
            return [
                ":simple-ocaml: opam (OCaml Package Manager)",
                f"[{cell(package.path.split('/')[2])}]({package})",
            ]
        if "github.com" in package.hostname:
            return [
                ":simple-github: GitHub Packages",
                f"[{cell(package.path.split('/')[5])}]({package})",
            ]
        return [f":octicons-package-16: [{cell(package.hostname)}]({package})", ""]

    def qiskit_requirements(self):
        """Qiskit requirements section: every qiskit constraint the project declares.

        One table rather than a block per package: the columns are the same wherever the
        constraint was read from, which is what makes them worth reading side by side.

        The Julia packages are not in it. Their `requires_qiskit` is a range of `Qiskit.jl`
        releases with none of the flags the other columns need behind it.
        """
        rows = []
        for package in self.project.pypi:
            rows.append(
                self._requirement_row(
                    f"PyPI [`{cell(package.package_name)}`]"
                    f"(../pypi/{package.package_name}.md)",
                    package,
                )
            )
        for package in self.project.python:
            rows.append(
                self._requirement_row(
                    f"repo [`{cell(package.package_name)}`]"
                    f"(../pip-source/{package.package_name}.md)",
                    package,
                )
            )
        for requirements in self.project.requirements or []:
            rows.append(
                self._requirement_row(
                    self._requirements_file_cell(requirements), requirements
                )
            )
        rows = [row for row in rows if row]
        if not rows:
            return []
        columns = [
            ("Declared in", "---"),
            ("Requires", ":---:"),
            ("V1", ":---:"),
            ("V2", ":---:"),
            ("Highest supported", ":---:"),
        ]
        return ["\n---\n### :simple-qiskit: Qiskit requirements\n"] + markdown_table(
            columns, rows
        )

    @classmethod
    def _requirement_row(cls, declared_in, package):
        """What a declaration asks of Qiskit, or None when it asks nothing"""
        if not package.requires_qiskit:
            return None
        version = package.highest_supported_qiskit_version
        return [
            declared_in,
            f"`{cell(package.requires_qiskit)}`",
            compatibility_mark(package.compatible_with_qiskit_v1),
            compatibility_mark(package.compatible_with_qiskit_v2),
            cls._release_cell(
                version,
                f"https://pypi.org/project/qiskit/{version}/",
                package.highest_supported_qiskit_release_date,
            ),
        ]

    def _requirements_file_cell(self, requirements):
        """A requirements file, linked on the default branch when the repository is known.

        The branch is not stored anywhere, so the link goes through HEAD.
        """
        github = self.project.github
        name = f"`{cell(requirements.file)}`"
        owner = getattr(github, "owner", None)
        repo = getattr(github, "repo", None)
        if not owner or not repo or not requirements.file:
            return name
        return (
            f"[{name}](https://github.com/{owner}/{repo}/blob/HEAD/{requirements.file})"
        )

    @staticmethod
    def _table(columns, rows):
        """A table of the Packages section, followed by the blank line that closes it"""
        lines = markdown_table(columns, rows)
        return lines + [""] if lines else []

    @staticmethod
    def _link_cell(text, url, title=None):
        """A link, with a tooltip in the title of the link itself.

        An `attr_list` tooltip is what the rest of the page uses, but it does not survive a
        value with a URL in it: `magiclink` turns that URL into a link inside the attribute
        list, and what is left is no longer one, so it renders as the braces it is written
        as. The title of the link has no such trouble, as long as the quotes a value
        carries of its own are escaped, which is what `tooltip` is for.
        """
        if not title:
            return f"[{text}]({url})"
        return f'[{text}]({url} "{tooltip(title)}")'

    @classmethod
    def _release_cell(cls, version, url, release_date=None):
        """A release as a table cell: the version, linked, with the date in its tooltip"""
        if not version:
            return ""
        if not url:
            return cell(version)
        return cls._link_cell(
            cell(version), url, f"Released: {release_date}" if release_date else None
        )

    @staticmethod
    def _count_cell(count):
        """A number of downloads or of users, as a table cell"""
        return f"{count:,}" if count else ""

    @staticmethod
    def _deferred_cell(value, deferred, field):
        """A manifest value, or a dash for the ones a manifest leaves to build time.

        `field` is what the manifest calls it, which is not what the section does: a
        `requires_python` comes from a `python_requires` keyword or a `requires-python`
        entry, and either of those is what `deferred` would name.
        """
        if value:
            return cell(value)
        if field.replace("_", "-") in (deferred or []) or field in (deferred or []):
            return '*&mdash;*{ title="computed at build time" }'
        return ""

    def write_page(self):
        """takes the lines and writes them down"""
        with mkdocs_gen_files.open(self.filename, "w") as f:
            print("\n".join(self.generate_all_lines()), file=f)
        mkdocs_gen_files.set_edit_path(
            self.filename,
            f"resources/members/{self.project.short_uuid}.toml",
        )

    def front_matter(self):
        """returns lines with front matter"""
        fm = []
        if self.project.status == "Qiskit Project":
            fm.append("icon: simple/qiskit")
        elif self.project.is_alumni:
            fm.append("icon: material/account-remove")
        elif self.project.status == "Under review":
            fm.append("icon: material/account-alert")
        elif self.project.status == "Unmaintained":
            fm.append("icon: material/heart-broken")
        elif self.project.status == "Early Project":
            fm.append("icon: material/sprout")
        elif self.project.status == "Very Early Project":
            fm.append("icon: material/seed")
        else:
            fm.append("icon: material/account")
        return ["---"] + fm + ["---"] if fm else []

    def title(self, main_title=None):
        """returns lines with title"""
        return [
            f"# {main_title or self.project.name} [:material-file-edit-outline:]"
            "(https://github.com/Qiskit/ecosystem/edit/main/resources/"
            f"members/{self.project.name_id}.toml)",
        ]

    def classification_card(self):  # pylint: disable=too-many-branches
        """Card with all the project classificaitons"""
        return ProjectSummaryCard.from_project(self.project).generate()

    def checkups(self):
        """Checkups table: one row per check up the project is not passing.

        The columns are what the check up itself knows. The project, its maturity and its
        status are on this page already, so they are not repeated here the way the tables in
        qisk.it/ecosystem-checkups list them."""
        lines = [
            "\n---\n",
            "### :material-list-status: Checkups",
            "\n",
        ]
        if not self.project.checks:
            lines.append(":material-check-all: All good")
            return lines
        columns = [
            ("Check up", "---"),
            ("Importance", ":---:"),
            ("What is failing", "---"),
            ("Days left", "---:"),
            ("Discussion", "---"),
        ]
        rows = [
            [
                f"[`[{checkup.id}]`](../checkups.md#{checkup.id})"
                f'{{ title="All the projects not passing check up [{checkup.id}]" }}'
                f" {CheckupAssets.cell(checkup.title)}",
                f":{checkup.importance_icon}:"
                f'{{ title="{CheckupAssets.tooltip(checkup.importance_description)}" }} '
                f"{CheckupAssets.cell(checkup.importance)}",
                # no details of its own (a source-based check up) means there is nothing to
                # add to the title in the column before
                CheckupAssets.cell(checkup.details) if checkup.details else "",
                self.days_left(self.project, checkup),
                self.discussion_cell(checkup),
            ]
            # the most severe first
            for checkup in sorted(
                self.project.checks.values(),
                key=lambda checkup: checkup.importance_rank,
            )
        ]
        # a column with nothing to say is left out, as in the check up page tables. For an
        # alumni project every cure period reads the same placeholder, which is one of them
        if all(row[3] == "&mdash;" for row in rows):
            for row in rows:
                row[3] = ""
        return lines + markdown_table(columns, rows)

    @staticmethod
    def days_left(project, checkup):
        """How long the check up can stay as it is, as a table cell.

        Both clocks are running on an explained check up: the cure period, and the day the
        explanation stops applying. The one that runs out last is the one that says when the
        check up needs attention again, so this is the larger of the two. There is nothing to
        count for an alumni project: its cure period is what retired it in the first place.
        """
        if project.is_alumni:
            return "&mdash;"
        # an explanation with no `xfailed_until` never expires, so there is no day to count to
        if checkup.cure_period_is_infinite or (
            checkup.xfailed and checkup.xfailed_until is None
        ):
            return "&infin;"
        days = [
            value
            for value in (
                checkup.days_left_in_cure_period,
                checkup.days_until_xfailed_expires,
            )
            if value is not None
        ]
        if not days:
            return "&mdash;"
        return str(max(days)) if max(days) >= 0 else "overdue"

    @staticmethod
    def discussion_cell(checkup):
        """Why the check up is not being acted on, as a table cell: the explanation that
        applies to it, when it has one, and the link to where it is being discussed.

        The explanation goes in as the Markdown it was written as, so a `[text](url)` or a
        `<url>` in a member file renders as a link. `pymdownx.magiclink` takes care of the
        URLs that were written as plain text (see `markdown_extensions` in properdocs.yml).
        """
        parts = []
        if checkup.xfail_applies:
            parts.append(CheckupAssets.cell(checkup.xfailed))
        link = CheckupAssets.discussion_link(checkup)
        if link:
            parts.append(link)
        return " &middot; ".join(parts)

    def badge(self):
        """Badge card"""
        if self.project.badge_md is None:
            return []
        lines = [
            "\n",
            "### :simple-shieldsdotio: Badge",
            "\n",
            '<div style="display: flex;"><button '
            ' title="Copy to clipboard" '
            'data-clipboard-target="#__code___code_0 &gt; code" '
            'data-md-type="copy">',
            f'<img src="{self.project.badge.url}">',
            '</button><pre style="width:600px; margin:0px" id="__code_0">'
            f'<code tabindex="0">{self.project.badge_md}</code></pre></div>',
            f"\n**Style** `{self.project.badge.style}`  \n Check out [Badges section]"
            "(../badges.md) to learn more about how badges are used for status communicaiton "
            "or on how to change the badge style.",
        ]
        return lines

    def urls_card(self):
        """List of URLs in the project metadata"""
        return URLsCard(self.project).generate()

    def description(self):
        """returns lines with description"""
        return [">", self.project.description] if self.project.description else []
