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

from datetime import datetime, timedelta
import json
import tomllib
import os
import re
from typing import Optional
from pathlib import Path
from jsonpath import findall, query
from slugify import slugify

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

        for classification in ["Member", "Qiskit Project", "Under revision", "Alumni"]:
            lines = [
                f'???{"+" if classification in ["Under revision", "Alumni"] else ""} note '
                f'"There are {len(projects[classification])} projects with this classification"'
            ]
            lines += [
                f"\n     - [{p.name}](../p/{p.short_uuid})"
                for p in projects[classification]
            ]
            writelines(classification, lines)

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
                    classification_singular.capitalize(): f"[{name}](#{section_name})",
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
                    f"\n     - [{p.name}](../p/{p.short_uuid})" for p in projects[name]
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

    def update_checkups(self, name=None, checker=None, update_all=False):
        """
        Updates checkups data.
        Args:
            name: If not given, runs on all the members. Otherwise, all the members with `name_id`
             that contains <name> as substring are checked.
            checker: It can be something like test_classifications.py::test_004 or nothing
            update_all: If False (default) runs on all project. Otherwise Alumni are excluded.
        """
        for project in self.dao.get_all(name):
            if project.status == "Alumni" and not update_all:
                # "Alumni" projects are not updated in their checkups
                continue
            project.update_checkups(checker=checker)
            if project.checks:
                for checkup_id, checkup in project.checks.items():
                    if checkup.xfailed:
                        self.logger.info(
                            "☑️ %s expected to fail checkup %s: %s ",
                            project.name,
                            checkup_id,
                            checkup.xfailed,
                        )
                        continue

                    cure_period_str = (
                        str(checkup.cure_period_in_days)
                        if checkup.cure_period_in_days >= 0
                        else "∞"
                    )
                    if checkup.cure_period_in_days < 0:
                        left_period_str = "∞"
                    else:
                        left_period_int = (
                            checkup.cure_period_in_days - checkup.days_since_failure
                        )
                        if left_period_int < 0:
                            left_period_str = "no"
                        else:
                            left_period_str = str(
                                checkup.cure_period_in_days - checkup.days_since_failure
                            )

                    for_x_days = (
                        f"for {checkup.days_since_failure} days, so "
                        f"{left_period_str} days left in the cure period"
                        if checkup.days_since_failure != 0
                        else "since today, "
                        f"so {cure_period_str}-day cure period starts now"
                    )
                    self.logger.info(
                        "%s %s (%s) failed checkup %s (%s)",
                        "💣" if checkup.importance == "CRITICAL" else "❌",
                        project.name,
                        project.name_id,
                        checkup_id,
                        for_x_days,
                    )
            else:
                self.logger.info(
                    "✅ %s (%s) passed all the checkups",
                    project.name,
                    project.name_id,
                )
            self.dao.update(project.name_id, checks=project.checks)

    def update_status(self, name=None, update_all=False):
        """
        Check if a project should be moved to "Under revision" or "Alumni"

        Args:
            name: project to udpate. None (default) if all of them.
            update_all: Updates all the projects. If False (default) will not
              update "Qiskit Project" or "Alumni"
        """
        for project in self.dao.get_all(name):
            if project.status in ["Qiskit Project", "Alumni"] and not update_all:
                # "Qiskit Project" status is governed differently,
                # not via checkups in Qiskit Ecosystem.
                # "Alumni" projects stay alumni
                continue

            if project.status == "Under revision":
                # reset "Under revision" status. It will be set back if it is still true.
                project.status = None

            for check in project.checks.values():
                if check.xfailed:
                    # Xfails do not affect the status
                    continue
                if check.cure_period_in_days is False:
                    # if cure_period_in_days is disabled (by cure_period_in_days = false), skip.
                    continue
                deadline = check.since + timedelta(days=check.cure_period_in_days)
                if datetime.today() > deadline:
                    # deadline passed
                    project.status = "Alumni"
                    break
                # still in cure period
                project.status = "Under revision"
            self.dao.update(project.name_id, status=project.status)

    def update_maturity(self, name=None):
        """Check if a project maturity should move to archived"""
        for project in self.dao.get_all(name):
            project.update_maturity()
            self.dao.update(project.name_id, maturity=project.maturity)

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
                if member.status != "Alumni"
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
