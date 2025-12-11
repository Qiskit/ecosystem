"""CliMembers class for controlling all CLI functions."""

import json
import tomllib
import os
from typing import Optional, Tuple
from pathlib import Path
from jsonpath import findall, query


from ecosystem.dao import DAO
from ecosystem.member import Member
from ecosystem.error_handling import logger
from ecosystem.validation import validate_member


class CliMembers:
    """CliMembers class.
    Entrypoint for all CLI members commands.

    Each public method of this class is CLI command
    and arguments for method are options/flags for this command.

    Ex: `python manager.py members update_badges`
    """

    def __init__(self, root_path: Optional[str] = None):
        """CliMembers class."""
        self.current_dir = root_path or os.path.abspath(os.getcwd())
        self.resources_dir = f"{self.current_dir}/ecosystem/resources"
        self.dao = DAO(path=self.resources_dir)
        self.logger = logger

    def validate(self, name=None):
        """validate members in <self.resources_dir>/members.
        If <name> is not given, runs on all the members.
        Otherwise, all the members with name_id that contains <name>
        as substring are checked.
        """
        for member in self.dao.get_all():
            if name and name not in member.name_id:
                continue
            passing, not_passing = validate_member(member)
            if not passing:
                logger.error("%s has no validations?", member.name_id)
            if not not_passing:
                logger.info("%s ✓", member.name_id)

    def add_repo_2db(
        self,
        repo_name: str,
        repo_link: str,
        repo_description: str,
        repo_licence: str,
        repo_contact: str,
        repo_alt: str,
        repo_affiliations: str,
        repo_labels: Tuple[str],
        repo_website: Optional[str] = None,
    ) -> None:
        """Adds repo to list of entries.

        Args:
            repo_name: repo name
            repo_link: repo url
            repo_description: repo description
            repo_contact: repo email
            repo_licence: repo licence
            repo_affiliations: repo university, company, ...
            repo_labels: comma separated labels
            repo_website: link to project website
        """

        new_repo = Member(
            repo_name,
            repo_link,
            repo_description,
            repo_licence,
            repo_contact,
            repo_alt,
            repo_affiliations,
            list(repo_labels),
            website=repo_website,
        )
        self.dao.write(new_repo)

    def update_badges(self):
        """Updates badges for projects."""
        for project in self.dao.get_all():
            # Create a json to be consumed by https://shields.io/badges/endpoint-badge
            data = {
                "schemaVersion": 1,
                "label": "Qiskit Ecosystem",
                "namedLogo": "Qiskit",
                "message": project.name,
                "color": "6929C4",
            }
            with open(
                os.path.join(self.current_dir, "badges", f"{project.short_uuid}"), "w"
            ) as outfile:
                json.dump(data, outfile, indent=4)
                self.logger.info("Badge for %s has been updated.", project.name)
            project.update_badge()
            self.dao.update(project.name_id, badge=project.badge)

    def update_badge_list(self):
        """Updates badge list in qisk.it/ecosystem-badges."""
        start_tag = "<!-- start:table-badge -->"
        end_tag = "<!-- end:table-badge -->"

        projects = []
        for project in self.dao.get_all():
            if project.badge is None:
                continue
            projects.append((project.name, project.badge, project.badge_md))

        projects.sort(key=lambda x: x[0].casefold())

        lines = [
            "",
            "<table>",
            '<tr><th width="10%">Member</th><th width="60%">Badge</th><th>MD Code</th></tr>',
        ]
        for name, badge, badge_md in projects:
            lines.append(
                "<tr>"
                f"<td>{name}</td>"
                f'<td><img src="{badge}" /></td>'
                f'<td><pre class="notranslate"><code>{badge_md}</code> &nbsp; </pre></td>'
                "</tr>"
            )
        lines.append("</table>\n")
        readme_md = os.path.join(self.current_dir, "badges", "README.md")

        with open(readme_md, "r") as readme_file:
            content = readme_file.read()

        to_replace = content[
            content.find(start_tag) + len(start_tag) : content.rfind(end_tag)
        ]

        new_content = content.replace(to_replace, "\n".join(lines))

        with open(readme_md, "w") as outfile:
            outfile.write(new_content)

    def update_github(self, name=None):
        """
        Updates GitHub data.
        If <name> is not given, runs on all the members.
        Otherwise, all the members with name_id that contains <name>
        as substring are checked.
        """
        for project in self.dao.get_all():
            if name and name not in project.name_id:
                continue
            project.update_github()
            self.dao.update(project.name_id, github=project.github)

    def update_pypi(self, name=None):
        """
        Updates PyPI data.
        If <name> is not given, runs on all the members.
        Otherwise, all the members with name_id that contains <name>
        as substring are checked.
        """
        for project in self.dao.get_all():
            if name and name not in project.name_id:
                continue
            project.update_pypi()
            self.dao.update(project.name_id, pypi=project.pypi)

    def update_julia(self):
        """Updates Julia data."""
        for project in self.dao.get_all():
            project.update_julia()
            self.dao.update(project.name_id, julia=project.julia)

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
            "url": "github.url",
            "description": ["description", "github.description"],
            "licence": ["licence", "github.license"],
            "contact_info": "contact_info",
            "affiliations": "affiliations",
            "labels": "labels",
            "group": "group",
            "category": "group",
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
                CliMembers.filter_data(member.to_dict(), member_data_to_export)
                for member in self.dao.get_all()
            ],
            "labels": CliMembers.load_labels_toml(
                Path(self.resources_dir, "labels.toml"), labels_data_to_export
            ),
        }
        Path(output_file).write_text(
            json.dumps(data, default=str, separators=(",", ":"), indent=4)
        )

    @staticmethod
    def load_labels_toml(filename, label_data_to_export):
        """loads labels.toml and returns a json with the mapping in label_data_to_export"""
        with open(filename, "rb") as f:
            data = tomllib.load(f)
        return CliMembers.filter_data(data, label_data_to_export)
