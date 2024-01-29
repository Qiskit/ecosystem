"""CliCI class for controlling all CLI functions."""
import os
from typing import Optional

import requests

from ecosystem.daos import DAO
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
