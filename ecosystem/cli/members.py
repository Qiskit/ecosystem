"""CliMembers class for controlling all CLI functions."""
import json
import os
from typing import Optional, Tuple

import requests

from ecosystem.daos import DAO
from ecosystem.models import Tier
from ecosystem.models.repository import Repository
from ecosystem.utils import logger


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
        self.resources_dir = "{}/ecosystem/resources".format(self.current_dir)
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
        repo_tier: Optional[str] = None,
        repo_website: Optional[str] = None,
    ) -> None:
        """Adds repo to list of entries.

        Args:
            repo_name: repo name
            repo_link: repo url
            repo_description: repo description
            repo_contact: repo email
            repo_alt: repo alternatives
            repo_licence: repo licence
            repo_affiliations: repo university, company, ...
            repo_labels: comma separated labels
            repo_tier: tier for repository
            repo_website: link to project website
        """

        new_repo = Repository(
            repo_name,
            repo_link,
            repo_description,
            repo_licence,
            repo_contact,
            repo_alt,
            repo_affiliations,
            list(repo_labels),
            tier=repo_tier or Tier.COMMUNITY,
            website=repo_website,
        )
        self.dao.write(new_repo)

    def update_badges(self):
        """Updates badges for projects."""
        badges_folder_path = "{}/badges".format(self.current_dir)

        for tier in Tier.all():
            for project in self.dao.get_repos_by_tier(tier):
                tests_passed = True
                for type_test in project.tests_results:
                    if type_test.test_type == "standard" and not type_test.passed:
                        tests_passed = False
                color = "blueviolet" if tests_passed else "gray"
                label = project.name
                message = tier
                url = (
                    f"https://img.shields.io/static/v1?"
                    f"label={label}&message={message}&color={color}"
                )

                shields_request = requests.get(url)
                with open(f"{badges_folder_path}/{project.name}.svg", "wb") as outfile:
                    outfile.write(shields_request.content)
                    self.logger.info("Badge for %s has been updated.", project.name)

    def update_stars(self):
        """Updates start for repositories."""
        for tier in Tier.all():
            for project in self.dao.get_repos_by_tier(tier):
                stars = None
                url = project.url[:-1] if project.url[-1] == "/" else project.url
                url_chunks = url.split("/")
                repo = url_chunks[-1]
                user = url_chunks[-2]

                response = requests.get(f"http://api.github.com/repos/{user}/{repo}")
                if not response.ok:
                    self.logger.warning("Bad response for project %s", project.url)
                    continue

                json_data = json.loads(response.text)
                stars = json_data.get("stargazers_count")
                self.dao.update(project.url, stars=stars)
                self.logger.info("Updating star count for %s: %d", project.url, stars)
