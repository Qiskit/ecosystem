"""CliTests class for controlling all CLI functions."""
from __future__ import annotations


import glob
import json
import os
import shutil
import uuid

import requests

from ecosystem.daos import DAO
from ecosystem.models.repository import Repository
from ecosystem.utils import logger, parse_submission_issue, set_actions_output


class CliTests:
    """CliTests class.
    Entrypoint for all CLI tests commands.

    Each public method of this class is CLI command
    and arguments for method are options/flags for this command.

    Ex: `python manager.py tests python_stable_tests --body="<SOME_MARKDOWN>"`
    """

    def __init__(self, root_path: str | None):
        """CliTests class."""
        self.current_dir = root_path or os.path.abspath(os.getcwd())
        self.resources_dir = "{}/ecosystem/resources".format(self.current_dir)
        self.dao = DAO(path=self.resources_dir)
        self.logger = logger

    def update_badges(self):
        """Updates badges for projects."""
        badges_folder_path = "{}/badges".format(self.current_dir)

        for project in self.dao.get_all():
            color = "blueviolet"
            label = project.name
            message = "Qiskit Ecosystem"
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
        for project in self.dao.get_all():
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

    @staticmethod
    def parser_issue(body: str) -> None:
        """Command for calling body issue parsing function.

        Args:
            body: body of the created issue

        Returns:
            logs output
            We want to give the result of the parsing issue to the GitHub action
        """

        parsed_result = parse_submission_issue(body)

        to_print = [
            ("SUBMISSION_NAME", parsed_result.name),
            ("SUBMISSION_REPO", parsed_result.url),
            ("SUBMISSION_DESCRIPTION", parsed_result.description),
            ("SUBMISSION_LICENCE", parsed_result.licence),
            ("SUBMISSION_CONTACT", parsed_result.contact_info),
            ("SUBMISSION_ALTERNATIVES", parsed_result.alternatives),
            ("SUBMISSION_AFFILIATIONS", parsed_result.affiliations),
            ("SUBMISSION_LABELS", parsed_result.labels),
            ("SUBMISSION_WEBSITE", parsed_result.website),
        ]

        set_actions_output(to_print)

    def add_repo_2db(
        self,
        repo_name: str,
        repo_link: str,
        repo_description: str,
        repo_licence: str,
        repo_contact: str,
        repo_alt: str,
        repo_affiliations: str,
        repo_labels: tuple[str],
        repo_website: str | None,
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
            website=repo_website,
        )
        self.dao.write(new_repo)
