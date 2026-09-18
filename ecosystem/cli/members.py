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

"""CliMembers class for controlling all CLI functions."""

import json
import tomllib
import os
import re
from typing import Optional
from pathlib import Path
from jsonpath import findall, query
from slugify import slugify

from ecosystem.check import ChecksToml, parse_exclusions
from ecosystem.dao import DAO
from ecosystem.classifications import ClassificationsToml
from ecosystem.error_handling import logger


class CliMembers:
    """CliMembers class.
    Entrypoint for all CLI members commands.

    Each public method of this class is CLI command
    and arguments for method are options/flags for this command.

    Ex: `python manager.py members update_badge`
    """

    def __init__(self, root_path: Optional[str] = None):
        """CliMembers class."""
        env_resources_dir = os.getenv("ECOSYSTEM_RESOURCES_DIR")
        self.current_dir = Path(root_path or Path.cwd())
        self.resources_dir = Path(env_resources_dir or self.current_dir / "resources")

        self.classifications_toml = ClassificationsToml(
            resources_dir=self.resources_dir
        )
        self.checks_toml = ChecksToml(resources_dir=self.resources_dir)
        self.dao = DAO(path=self.resources_dir)
        self.logger = logger

    def create_badge_endpoints(
        self, name: str = None, example: str = None, output_directory: str = None
    ):  # pylint: disable=too-many-locals
        """Creates the JSON files in to be deployed in qiskit.github.io/ecosystem/b/<jsonfile>
         so they can be consumed by
        https://img.shields.io/endpoint?url=https://qiskit.github.io/ecosystem/b/<jsonfile>

        Args:
            name: If <name> is not given, runs on all the members. Otherwise, all the members
                with name_id that contains <name> as substring are updated.
            example: If given, creates example badges for a ficticious project with that name. For
                example -e "Qiskit Banana Compiler" is currectly used in qisk.it/ecosystem-badges
                as an example. If not given, it does not create the example endpoints.
            output_directory: directory in which it saves the json files. By default, ./badges
        """
        default_schemaversion = 1
        default_label = "Qiskit Ecosystem"
        alumni_label = f"{default_label} Alumni"
        default_namedlogo = "Qiskit"
        default_color = "6929C4"
        warning_color = "c46929"
        default_iserror = "true"
        default_style = "flat"
        if not output_directory:
            output_directory = os.path.join(self.current_dir, "badges")
        Path(output_directory).mkdir(parents=True, exist_ok=True)
        if example:
            for style in ["flat", "flat-square", "plastic", "for-the-badge", "social"]:
                data = {
                    "schemaVersion": default_schemaversion,
                    "label": default_label,
                    "namedLogo": default_namedlogo,
                    "message": example,
                    "color": default_color,
                    "isError": default_iserror,
                    "style": style,
                }
                filename = f"example_{style}"
                with open(os.path.join(output_directory, filename), "w") as outfile:
                    json.dump(data, outfile, indent=4)
                    self.logger.info(
                        "Example Badge endpoint (style=%s): %s",
                        style,
                        os.path.join(output_directory, filename),
                    )
            data_alumni = {
                "schemaVersion": default_schemaversion,
                "label": alumni_label,  # <-
                "namedLogo": default_namedlogo,
                "message": example,
                "color": default_color,
                "isError": default_iserror,
                "style": default_style,
            }
            filename = "example_alumni"
            with open(os.path.join(output_directory, filename), "w") as outfile:
                json.dump(data_alumni, outfile, indent=4)
                self.logger.info(
                    "Example Badge endpoint (status=Alumni): %s",
                    os.path.join(output_directory, filename),
                )

            data_under_revision = {
                "schemaVersion": default_schemaversion,
                "label": default_label,
                "namedLogo": default_namedlogo,
                "message": "Under revision",  # <-
                "color": warning_color,
                "isError": default_iserror,
                "style": default_style,
            }
            filename = "example_under-revision"
            with open(os.path.join(output_directory, filename), "w") as outfile:
                json.dump(data_under_revision, outfile, indent=4)
                self.logger.info(
                    "Example Badge endpoint (status=Under review): %s",
                    os.path.join(output_directory, filename),
                )
        for project in self.dao.get_all(name):
            # Create a json to be consumed by https://shields.io/badges/endpoint-badge
            if project.badge is None:
                continue

            is_alumni = None
            if project.status == "Alumni":
                is_alumni = alumni_label

            status_color = None
            if project.status == "Under revision":
                # if status is "Under revision", set status color to orange as a warning.
                # Color from triadic palette:  https://www.color-hex.com/color/6929c4
                status_color = warning_color

            data = {
                "schemaVersion": project.badge.schemaVersion or default_schemaversion,
                "label": project.badge.label or is_alumni or default_label,
                "namedLogo": default_namedlogo,
                "message": project.badge.message or project.name,
                "color": project.badge.color or status_color or default_color,
                "isError": project.badge.isError or "true",
                "style": project.badge.style or "flat",
            }
            with open(
                os.path.join(output_directory, str(project.short_uuid)), "w"
            ) as outfile:
                json.dump(data, outfile, indent=4)
                self.logger.info(
                    "Badge endpoint %s for %s",
                    os.path.join(output_directory, str(project.short_uuid)),
                    project.name,
                )

    def update_docs_assets(self):
        """Updates the files in docs/assets/ to build the docs"""
        projects_per_classification = self._all_projects_classifications(
            "status", "maturity", "category", "labels", "interfaces"
        )
        self.update_badge_list()
        self.update_assets_status(projects_per_classification["status"])
        self.update_assets_maturity(projects_per_classification["maturity"])
        self.update_assets_categories(projects_per_classification["category"])
        self.update_assets_labels(projects_per_classification["labels"])
        self.update_assets_interfaces(projects_per_classification["interfaces"])
        self.update_assets_checkups()

    def update_assets_checkups(self):
        """Updates the check up tables in docs/assets/ from resources/checks.toml.

        Three fragments are generated, so the documentation never drifts from checks.toml:
        `checkups.md` (one row per check up), `checkup-importance.md` (the importance levels
        and their default cure period) and `checkup-categories.md` (the categories).
        """
        assets_dir = Path(self.current_dir, "docs", "assets")
        assets_dir.mkdir(parents=True, exist_ok=True)

        def cell(text):
            """A string that is safe to use inside a Markdown table cell"""
            return str(text).replace("|", "\\|").replace("\n", " ")

        def tooltip(text):
            """A string that is safe to use inside a Markdown attr_list title="..." """
            return cell(text).replace('"', "&quot;")

        # one row per check up
        checkups = dict(sorted(self.checks_toml.checkups.items()))
        lines = [
            "| id | check up | applies to | category | importance | cure period |",
            "| :---: | --- | --- | :---: | :---: | :---: |",
        ]
        for id_, checkup in checkups.items():
            importance = checkup.get("importance")
            importance_level = (
                self.checks_toml.importance(importance) if importance else {}
            )
            icon = importance_level.get("icon", "")
            importance_description = importance_level.get("description", "")
            lines.append(
                f'| <span id="{id_}">`[{id_}]`</span>'
                f' | {cell(checkup["title"])}<br>{cell(checkup["description"])}'
                f' | {cell(checkup.get("applies_to", "all"))}'
                f' | [{cell(checkup["category"])}](#{slugify(checkup["category"])})'
                f' | :{icon}:{{ title="{tooltip(importance_description)}" }}'
                f" [{cell(importance)}](#{slugify(importance)})"
                f" | {self._cure_period_cell(id_)} |"
            )
        Path(assets_dir, "checkups.md").write_text("\n".join(lines) + "\n")

        # the importance levels
        lines = [
            "| importance | description | cure period |",
            "| :---: | --- | :---: |",
        ]
        for importance in self.checks_toml.importances:
            icon = importance.get("icon", "")
            lines.append(
                f'| :{icon}: <span id="{slugify(importance["name"])}">'
                f'**{cell(importance["name"])}**</span>'
                f' | {cell(importance["description"])}'
                f' | {self._cure_period_str(importance.get("cure_period_in_days"))} |'
            )
        Path(assets_dir, "checkup-importance.md").write_text("\n".join(lines) + "\n")

        # the categories
        lines = ["| category | description |", "| :---: | --- |"]
        for category in self.checks_toml.categories:
            lines.append(
                f'| <span id="{slugify(category["name"])}">**{cell(category["name"])}**</span>'
                f' | {cell(category["description"])} |'
            )
        Path(assets_dir, "checkup-categories.md").write_text("\n".join(lines) + "\n")

    @staticmethod
    def _cure_period_str(days):
        """A `cure_period_in_days` value as a table cell"""
        if days is None:
            return "not defined"
        if days < 0:
            return "no deadline"
        if days == 0:
            return "none"
        return f"{days} days"

    def _cure_period_cell(self, checkup_id):
        """The effective cure period of a check up, noting when it overrides its importance"""
        checkup = self.checks_toml.checkup(checkup_id)
        if "cure_period_in_days" not in checkup:
            importance = checkup.get("importance")
            if not importance:
                return "not defined"
            return self._cure_period_str(
                self.checks_toml.importance(importance).get("cure_period_in_days")
            )
        return f'{self._cure_period_str(checkup["cure_period_in_days"])} \u26a0\ufe0f'

    def _all_projects_classifications(self, *classifications):
        """
        <classifications> is a list of attributes in each project to extract.
        Returns a dict with each of the classification as a key and, as value, a dict
        with {classification_name: Project}
        """

        classification_summary = {}
        for classification in classifications:
            classification_summary[classification] = {
                i: []
                for i in getattr(self.classifications_toml, f"{classification}_names")
            }
            classification_summary[classification][None] = []
        for project in self.dao.get_all():
            for classification in classifications:
                value = getattr(project, classification)
                if isinstance(value, list):
                    if len(value) == 0:
                        classification_summary[classification][None].append(project)
                    for each_value in value:
                        if each_value in classification_summary[classification]:
                            classification_summary[classification][each_value].append(
                                project
                            )
                        else:
                            classification_summary[classification][None].append(project)
                else:
                    if value in classification_summary[classification]:
                        classification_summary[classification][value].append(project)
                    else:
                        classification_summary[classification][None].append(project)
        return classification_summary

    def update_assets_status(self, projects):
        """Updates status.json and status.md docs/assets/"""
        projects["Member"] += projects[None]
        del projects[None]

        self.update_assets_classification("status", "status classification", projects)
        assets_dir = os.path.join(self.current_dir, "docs", "assets")

        def writelines(classification, lines):
            classification_md = os.path.join(
                assets_dir, f"{slugify(classification)}.md"
            )
            os.makedirs(os.path.dirname(classification_md), exist_ok=True)
            Path(classification_md).touch(exist_ok=True)

            with open(classification_md, "w") as outfile:
                outfile.writelines(lines)

        for classification in [
            "Member",
            "Qiskit Project",
            "Unmaintained",
            "Under revision",
            "Alumni",
        ]:
            lines = [
                f'???{"+" if classification in ["Under revision", "Alumni"] else ""} note '
                f'"There are {len(projects[classification])} projects with this classification"'
            ]
            lines += [
                f"\n     - [{p.name}](p/{p.short_uuid}.md)"
                for p in projects[classification]
            ]
            writelines(classification, lines)

        # "Early Project" and "Very Early Project" only differ on the age of the
        # repository, so they share a single table (youngest project first).
        early_projects = sorted(
            projects["Early Project"] + projects["Very Early Project"],
            key=lambda p: (p.age_in_months is None, p.age_in_months or 0),
        )
        lines = [
            f'??? note "There are {len(early_projects)} projects with these statuses"'
        ]
        if early_projects:
            lines += [
                "\n     | Project | Status | Repository created | Age (months) |",
                "\n     | --- | --- | --- | --- |",
            ]
            lines += [
                f"\n     | [{p.name}](p/{p.short_uuid}.md) | {p.status} "
                f"| {getattr(p.github, 'created_at', '')} | {p.age_in_months} |"
                for p in early_projects
            ]
        writelines("early-projects", lines)

    def update_assets_maturity(self, projects):
        """Updates maturity.json and maturity.md docs/assets/"""
        self.update_assets_classification("maturity", "maturity level", projects)

    def update_assets_categories(self, projects):
        """Updates category.json and categories.md docs/assets/"""
        self.update_assets_classification("category", "category", projects)

    def update_assets_labels(self, projects):
        """Updates labels.json and labels.md docs/assets/"""
        self.update_assets_classification("labels", "label", projects)

    def update_assets_interfaces(self, projects):
        """Updates interfaces.json and interfaces.md docs/assets/"""
        self.update_assets_classification("interfaces", "interface", projects)

    def update_assets_classification(
        self, classification, classification_singular, projects
    ):
        """Updates docs/assets/<classification>.json and docs/assets/<classification>.md"""
        assets_dir = os.path.join(self.current_dir, "docs", "assets")

        classification_json = os.path.join(assets_dir, f"{classification}.json")
        os.makedirs(os.path.dirname(classification_json), exist_ok=True)
        Path(classification_json).touch(exist_ok=True)

        classification_md = os.path.join(assets_dir, f"{classification}.md")
        os.makedirs(os.path.dirname(classification_md), exist_ok=True)
        Path(classification_md).touch(exist_ok=True)

        short_description = []
        lines = []

        classification_names = sorted(
            getattr(self.classifications_toml, f"{classification}_names")
        )
        for other in ["Other", "Other interface", "Other language"]:
            if other in classification_names:
                classification_names.append(
                    classification_names.pop(classification_names.index(other))
                )

        for name in classification_names:
            description = getattr(
                self.classifications_toml, f"{classification}_descriptions"
            )[name]
            section_name = getattr(
                self.classifications_toml, f"{classification}_sections"
            )[name] or slugify(name)
            section_text_md = os.path.join(
                self.resources_dir, classification, f"{section_name}.md"
            )
            short_description.append(
                {
                    classification_singular.capitalize(): f"[{name}](#{slugify(name, '-')})",
                    "Short description": description or "",
                }
            )
            if os.path.isfile(section_text_md):
                with open(section_text_md, "r") as file:
                    description = file.read()
            lines += [
                f"## {name}",
                "\n\n",
            ]
            if len(projects[name]):
                lines.append(
                    f'??? note "There are {len(projects[name])} projects with this classification"'
                )
                lines += [
                    f"\n     - [{p.name}](p/{p.short_uuid}.md)" for p in projects[name]
                ]
            else:
                lines.append("**No project with this classification**")
            lines += ["\n\n", description, "\n\n"]

        with open(classification_json, "w") as f:
            json.dump(short_description, f)

        with open(classification_md, "w") as outfile:
            outfile.writelines(lines)

    def update_badge_list(self):
        """Updates badge list in qisk.it/ecosystem-badges."""
        output_file = os.path.join(
            self.current_dir, "docs", "assets", "badges_table.md"
        )
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        Path(output_file).touch(exist_ok=True)

        projects = []
        for project in self.dao.get_all():
            if project.badge is None:
                self.logger.warning(
                    "badge not found for %s (%s)",
                    project.name_id,
                    project.name,
                )
                continue
            projects.append(
                (project.name, project.badge.url, project.badge_md, project.name_id)
            )

        projects.sort(key=lambda x: re.sub("[^A-Za-z0-9]+", "", x[0]).lower())

        lines = [
            "",
            "<table>",
            "<tr><th>Member</th><th>Badge (click for full size) and MarkDown code</th></tr>",
            "",
        ]
        for name, badge, badge_md, name_id in projects:
            lines.append(
                '<tr><td><a href="https://github.com/Qiskit/ecosystem/tree/main'
                f'/resources/members/{name_id}.toml">{name}</a></td>'
                f'<td><a href="{badge}"><img src="{badge}" /></a><br/>'
                f"\n\n```markdown\n{badge_md}   \n```\n\n</td>"
                "</tr>"
            )
        lines.append("</table>\n")

        with open(output_file, "w") as outfile:
            outfile.writelines(lines)

    def update_badge(self, name=None):
        """
        Updates Badge data.
        If <name> is not given, runs on all the members.
        Otherwise, all the members with name_id that contains <name>
        as substring are updated.
        """
        for project in self.dao.get_all(name):
            project.update_badge()
            self.dao.update(project.name_id, badge=project.badge)

    def update_github(self, name=None):
        """
        Updates GitHub data.
        If <name> is not given, runs on all the members.
        Otherwise, all the members with name_id that contains <name>
        as substring are checked.
        """
        for project in self.dao.get_all(name):
            project.update_github()
            self.dao.update(project.name_id, github=project.github)

    def update_pypi(self, name=None):
        """
        Updates PyPI data.
        If <name> is not given, runs on all the members.
        Otherwise, all the members with name_id that contains <name>
        as substring are checked.
        """
        for project in self.dao.get_all(name):
            project.update_pypi()
            self.dao.update(project.name_id, pypi=project.pypi)

    def update_julia(self, name=None):
        """
        Updates Julia data.

        If <name> is not given, runs on all the members.
        Otherwise, all the members with name_id that contains <name>
        as substring are checked.
        """
        for project in self.dao.get_all(name):
            project.update_julia()
            self.dao.update(project.name_id, julia=project.julia)

    def update_checkups(self, name=None, checker=None, exclude: str = None):
        """
        Updates checkups data.
        Args:
            name: If not given, runs on all the members. Otherwise, all the members with `name_id`
             that contains <name> as substring are checked.
            checker: It can be something like test_classifications.py::test_004 or nothing
            exclude: comma-separated list of membership statuses to leave out, like `-e alumni`.
              Projects already in one of them keep the check up data they have. The values are
              slugified, as in `update_status`, but only statuses have an effect here: this
              command is what runs the check ups, so an importance or a category has nothing
              to exclude yet.
        """
        exclude_set = parse_exclusions(exclude)
        for project in self.dao.get_all(name):
            if project.status and slugify(project.status) in exclude_set:
                # this membership status is excluded, so the project is left alone
                continue
            expired_xfails = {
                checkup_id: checkup
                for checkup_id, checkup in project.checks.items()
                if checkup.xfailed and checkup.xfailed_expired
            }
            project.update_checkups(checker=checker)
            for checkup_id, checkup in expired_xfails.items():
                self.logger.info(
                    "⌛ %s (%s) checkup %s: the explanation expired on %s, "
                    "so it is checked as a regular one from now on (%s)",
                    project.name,
                    project.name_id,
                    checkup_id,
                    checkup.xfailed_until,
                    checkup.xfailed,
                )
            if project.checks:
                for checkup_id, checkup in project.checks.items():
                    self._log_checkup(project, checkup_id, checkup)
            else:
                self.logger.info(
                    "✅ %s (%s) passed all the checkups",
                    project.name,
                    project.name_id,
                )
            self.dao.update(project.name_id, checks=project.checks)

    def _log_checkup(self, project, checkup_id, checkup):
        """Logs a check up that a project is not passing: either it is expected to fail
        (and until when the explanation for it is valid) or how much of the cure period is left.
        """
        if checkup.xfailed:
            if checkup.xfailed_until is None:
                expiration = "the explanation does not expire"
            else:
                expiration = (
                    f"the explanation expires on {checkup.xfailed_until}, "
                    f"in {checkup.days_until_xfailed_expires} days"
                )
            self.logger.info(
                "☑️ %s expected to fail checkup %s: %s (%s)",
                project.name,
                checkup_id,
                checkup.xfailed,
                expiration,
            )
            return

        cure_period_str = (
            "∞" if checkup.cure_period_is_infinite else str(checkup.cure_period_in_days)
        )
        if checkup.cure_period_is_infinite:
            left_period_str = "∞"
        else:
            left_period_int = checkup.cure_period_in_days - checkup.days_since_failure
            if left_period_int < 0:
                left_period_str = "no"
            else:
                left_period_str = str(left_period_int)

        for_x_days = (
            f"for {checkup.days_since_failure} days, so "
            f"{left_period_str} days left in the cure period"
            if checkup.days_since_failure != 0
            else f"since today, so {cure_period_str}-day cure period starts now"
        )
        self.logger.info(
            "%s %s (%s) failed checkup %s (%s)",
            "💣" if checkup.importance == "CRITICAL" else "❌",
            project.name,
            project.name_id,
            checkup_id,
            for_x_days,
        )

    def update_status(  # pylint: disable=too-many-branches
        self, name=None, exclude: str = None
    ):
        """
        Check if a project should be moved to (in order of precedence):
          -  "Alumni": If the cure period of a check up has expired
          - "Under revision": if there is a pending check up (cure period not expired)
          - "(Very) Early Project": if the project is young and has no pending check up
          - "Unmaintained": if the project declares no maintenance expectations (maturity in
            `as-is` or `deprecated`) and has no pending check up
        See docs/status.md

        Args:
            name: project to udpate. None (default) if all of them.
            exclude: comma-separated list of things to leave out, like
              `-e "recommendation, legacy, alumni"`. Each value is either

                - a check up importance or category, meaning "do not update the status because
                  of a check up of this importance or category", or
                - a membership status, meaning "leave the projects that are already in this
                  status alone". `-e "qiskit-project, alumni"` is the usual pair: "Qiskit
                  Project" is governed differently, and "Alumni" projects stay alumni.

              The values are slugified, so `-e "Best Practice"` and `-e best_practice` are
              the same thing.
        """
        exclude_set = parse_exclusions(exclude)
        for project in self.dao.get_all(name):
            if project.status and slugify(project.status) in exclude_set:
                # this membership status is excluded, so the project is left alone
                continue

            if project.status in [
                "Under revision",
                "Unmaintained",
                "Early Project",
                "Very Early Project",
            ]:
                # reset the derived statuses. They will be set back if they are still true.
                project.status = None

            for check in project.checks.values():
                if check.xfail_applies:
                    # Xfails do not affect the status, unless their explanation expired
                    continue
                if exclude_set & {slugify(check.importance), slugify(check.category)}:
                    # the importance or the category of the check up is excluded, so it
                    # does not count towards the status
                    continue
                if check.cure_period_expired:
                    # deadline passed. An infinite cure period (a negative
                    # cure_period_in_days) never expires, so it never gets here
                    project.status = "Alumni"
                    break
                # still in cure period
                project.status = "Under revision"

            if project.status is None and project.unmaintained:
                # the project declares no maintenance expectations
                project.status = "Unmaintained"

            if project.status is None:
                # no pending check up, so the status only depends on how old the repository is
                if project.very_early:
                    project.status = "Very Early Project"
                elif project.early:
                    project.status = "Early Project"

            self.dao.update(project.name_id, status=project.status)

    @staticmethod
    def filter_data(
        member_dict, data_map, forced_addition=False
    ):  # pylint: disable=too-many-branches
        """takes a member dictionary and a data map,
        and returns a dict that is filtered by the map.
        If forced_addition is True, all the elements of the
        data_map will be added, even if they are empty"""
        filtered_data = {}
        for key, alias in data_map.items():
            if isinstance(alias, dict):
                data = CliMembers.filter_data(member_dict, alias)
                if data:
                    filtered_data[key] = data
            elif isinstance(alias, tuple):
                if len(alias) != 2:
                    raise ValueError(
                        "%s malformed. "
                        "It needs to have exactly two elements,one "
                        "with the query, the otherone with the selector"
                    )
                data = list(query(alias[0], member_dict).select(*alias[1]))
            elif isinstance(alias, list):
                # a list of alias in priority in case they do not exist
                for candidate_alias in alias:
                    candidate_value = CliMembers.filter_data(
                        member_dict, {key: candidate_alias}
                    )
                    if len(candidate_value) == 1:
                        data = list(candidate_value.values())[0]
                        break
            else:
                found_all = findall(alias, member_dict)
                if len(found_all) == 0:
                    data = None
                elif len(found_all) == 1:
                    data = found_all[0]
                else:
                    raise ValueError(
                        f"I dont know who to hangle multiple results for {found_all}. "
                        "Maybe functools.reduce?"
                    )
            if forced_addition or data:
                filtered_data[key] = data
        return filtered_data

    def compile_json(self, output_file: str):
        """Compile JSON file (v0) for consumption by ibm.com"""
        member_data_to_export = {
            "uuid": "uuid",
            "name": "name",
            "url": ["github.url", "url"],
            "description": ["description", "github.description"],
            "licence": ["licence", "github.license"],
            "contact_info": "contact_info",
            "affiliations": "affiliations",
            "labels": "labels",
            "group": "category",
            "category": "category",
            "stars": "github.stars",
            "documentation": "documentation",
            "website": "website",
            "reference_paper": "reference_paper",
            "ibm_maintained": "ibm_maintained",
            "badge": "badge",
            "websites": {
                "home": "website",
                "documentation": "documentation",
                "reference_paper": "reference_paper",
            },
            "github": {
                "url": "github.url",
                "stars": "github.stars",
                "last_commit": "github.last_commit",
                "last_activity": "github.last_activity",
                "total_dependent_packages": "github.total_dependent_packages",
                "total_dependent_repositories": "github.total_dependent_repositories",
                "estimated_contributors": "github.estimated_contributors",
                "archived": "github.archived",
            },
            "python_packages": (
                "pypi.*",
                [
                    "package_name",
                    "version",
                    "url",
                    "compatible_with_qiskit_v1",
                    "compatible_with_qiskit_v2",
                    "last_month_downloads",
                    "highest_supported_qiskit_version",
                    "highest_supported_qiskit_release_date",
                ],
            ),
        }
        # {"Types": [{"name": ..., "description": ...}],
        #  "Subjects": [{"name": ..., "description": ...}]}
        labels_data_to_export = {
            "Types": (
                "categories.*",
                [
                    "name",
                    "description",
                ],
            ),
            "Subjects": (
                "labels.*",
                [
                    "name",
                    "description",
                ],
            ),
        }
        data = {
            "meta": {
                "version": 1,
                "deprecated fields": {
                    "members.created_at": "currently not in use. To be removed in v2.",
                    "members.updated_at": "currently not in use. To be removed in v2.",
                    "members.contact_info": "currently not in use. To be removed in v2.",
                    "members.affiliations": "currently not in use. To be removed in v2.",
                    "members.group": "replaced by members.category. To be removed in v2.",
                    "members.stars": "replaced by members.github.stars. To be removed in v2.",
                    "members.url": "replaced by members.github.url. To be removed in v2.",
                    "members.website": "replaced by members.website.home. To be removed in v2.",
                    "reference_paper": "replaced by members.website.reference_paper. "
                    "To be removed in v2.",
                },
            },
            "members": [
                CliMembers.filter_data(
                    member.to_dict(),
                    member_data_to_export,
                )
                for member in self.dao.get_all()
                if member.status not in ["Alumni", "Very Early Project"]
            ],
            "labels": CliMembers.load_classifications_toml(
                Path(self.resources_dir, "classifications.toml"), labels_data_to_export
            ),
        }
        Path(output_file).write_text(
            json.dumps(data, default=str, separators=(",", ":"), indent=4)
        )

    @staticmethod
    def load_classifications_toml(filename, label_data_to_export):
        """loads classifications.toml and returns a json with the mapping in label_data_to_export"""
        with open(filename, "rb") as f:
            data = tomllib.load(f)
        return CliMembers.filter_data(data, label_data_to_export)
