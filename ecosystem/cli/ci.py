"""CliCI class for controlling all CLI functions."""
import os
from typing import Optional

import requests

from ecosystem.daos import DAO
from ecosystem.models import Tier
from ecosystem.utils import logger, parse_submission_issue
from ecosystem.utils.utils import set_actions_output


class CliCI:
    """CliCI class.
    Entrypoint for all CLI CI commands.

    Each public method of this class is CLI command
    and arguments for method are options/flags for this command.

    Ex: `python manager.py ci parser_issue --body="<SOME_MARKDOWN>"`
    """

    def __init__(self, root_path: Optional[str] = None):
        """CliCI class."""
        self.current_dir = root_path or os.path.abspath(os.getcwd())
        self.resources_dir = "{}/ecosystem/resources".format(self.current_dir)
        self.dao = DAO(path=self.resources_dir)
        self.logger = logger

    def dispatch_check_workflow(
        self,
        repo_url: str,
        branch_name: str,
        tier: str,
        token: str,
        owner: str = "qiskit-community",
        repo: str = "ecosystem",
    ) -> bool:
        """Dispatch event to trigger check workflow.

        Args:
            repo_url: url of the repo
            branch_name: name of the branch
            tier: tier of the project
            token: token base on the date
            owner: "qiskit-community" parameters
            repo: "ecosystem"

        Return: true
        """
        url = "https://api.github.com/repos/{owner}/{repo}/dispatches".format(
            owner=owner, repo=repo
        )
        repo_split = repo_url.split("/")
        repo_name = repo_split[-1]

        # run each type of tests in same workflow
        response = requests.post(
            url,
            json={
                "event_type": "check_project",
                "client_payload": {
                    "repo_url": repo_url,
                    "repo_name": repo_name,
                    "branch_name": branch_name,
                    "tier": tier,
                },
            },
            headers={
                "Authorization": "token {}".format(token),
                "Accept": "application/vnd.github.v3+json",
            },
        )
        if response.ok:
            self.logger.info("Success response on dispatch event. %s", response.text)
        else:
            self.logger.warning(
                "Something wend wrong with dispatch event: %s", response.text
            )
        return True

    def expose_all_project_to_actions(self):
        """Exposes all project for github actions."""
        repositories = []
        tiers = []
        for tier in Tier.non_main_tiers():
            for repo in self.dao.get_repos_by_tier(tier):
                if not repo.skip_tests:
                    repositories.append(repo.url)
                    tiers.append(repo.tier)
        set_actions_output(
            [("repositories", ",".join(repositories)), ("tiers", ",".join(tiers))]
        )

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
