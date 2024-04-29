"""CliCI class for controlling all CLI functions."""
from pathlib import Path
from typing import Optional

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

    @staticmethod
    def add_member_from_issue(body: str) -> None:
        """Parse an issue created from the issue template and add the member to the database

        Args:
            body: body of the created issue

        Returns:
            None (side effect is updating database)
        """

        current_dir = Path.cwd()
        resources_dir = Path(current_dir, "ecosystem/resources")

        parsed_result = parse_submission_issue(body, current_dir)
        DAO(path=resources_dir).write(parsed_result)
        set_actions_output([ ("SUBMISSION_NAME", parsed_result.name) ])
