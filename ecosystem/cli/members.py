"""CliMembers class for controlling all CLI functions."""

import json
import os
from typing import Optional, Tuple
from pathlib import Path
from jsonpath import findall, query


from ecosystem.dao import DAO
from ecosystem.submission import Submission
from ecosystem.error_handling import logger


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

        new_repo = Submission(
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

    def update_github(self):
        """Updates GitHub data."""
        for project in self.dao.get_all():
            project.update_github()
            self.dao.update(project.name_id, stars=project.github.stars)
            self.dao.update(project.name_id, github=project.github)

    def update_pypi(self):
        """Updates PyPI data."""
        for project in self.dao.get_all():
            project.update_pypi()
            self.dao.update(project.name_id, pypi=project.pypi)

    @staticmethod
    def filter_member_data(member_dict, data_map):
        """takes a member dictionary and a data map,
        and returns a dict that is filtered by the map"""
        filtered_data = {}
        for key, alias in data_map.items():
            if isinstance(alias, dict):
                data = CliMembers.filter_member_data(member_dict, alias)
                if data:
                    filtered_data[key] = data
            elif isinstance(alias, list):
                if len(alias) != 2:
                    raise ValueError(
                        "%s malformed. "
                        "It needs to have exactly two elements,one "
                        "with the query, the otherone with the selector"
                    )
                data = list(query(alias[0], member_dict).select(*alias[1]))

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
            if data:
                filtered_data[key] = data
        return filtered_data

    def compile_json(self, output_file: str):
        """Compile JSON file (v0) for consumption by ibm.com"""
        member_data_to_export = {
            "uuid": "uuid",
            "name": "name",
            "url": "github.url",
            "description": "description",
            "licence": "licence",
            "contact_info": "contact_info",
            "affiliations": "affiliations",
            "labels": "labels",
            "created_at": "created_at",
            "updated_at": "updated_at",
            "group": "group",
            "stars": "github.stars",
            "documentation": "documentation",
            "website": "website",
            "reference_paper": "reference_paper",
            "ibm_maintained": "ibm_maintained",
        }
        data = {
            "members": [
                CliMembers.filter_member_data(member.to_dict(), member_data_to_export)
                for member in self.dao.get_all()
            ],
            "labels": json.loads(Path(self.resources_dir, "labels.json").read_text()),
        }
        Path(output_file).write_text(
            json.dumps(data, default=str, separators=(",", ":"))
        )

    def compile_json_v1(self, output_file: str):
        """Compile JSON file (v1) for consumption by ibm.com"""
        member_data_to_export = {
            "name": "name",
            "description": "description",
            "licence": "licence",
            "subjects": "labels",
            "type": "group",
            "badge": "badge",
            "ibm_maintained": "ibm_maintained",
            "websites": {
                "home": "website",
                "documentation": "documentation",
                "reference_paper": "reference_paper",
            },
            "github": {
                "url": "github.url",
                "stars": "github.stars",
                "last_commit": "github.last_commit",
            },
            "python_packages": [
                "pypi.*",
                [
                    "package_name",
                    "version",
                    "url",
                    "compatible_with_qiskit_v1",
                    "compatible_with_qiskit_v2",
                ],
            ],
        }
        data = {
            "members": [
                CliMembers.filter_member_data(member.to_dict(), member_data_to_export)
                for member in self.dao.get_all()
            ],
            "labels": json.loads(Path(self.resources_dir, "labels.json").read_text()),
        }
        Path(output_file).write_text(
            json.dumps(data, default=str, separators=(",", ":"), indent=4)
        )
