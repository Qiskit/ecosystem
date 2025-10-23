"""CliMembers class for controlling all CLI functions."""

import json
import os
from typing import Optional, Tuple
from pathlib import Path

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

    def update_stars(self):
        """Updates start for repositories."""
        for project in self.dao.get_all():
            project.update_github()
            stars = project.github.stars
            self.dao.update(project.name_id, stars=stars)
            self.dao.update(project.name_id, section="github", stars=stars)

    def compile_json(self, output_file: str):
        """Compile JSON file for consumption by ibm.com"""
        data = {
            "members": [repo.to_dict() for repo in self.dao.get_all()],
            "labels": json.loads(Path(self.resources_dir, "labels.json").read_text()),
        }
        Path(output_file).write_text(json.dumps(data))
