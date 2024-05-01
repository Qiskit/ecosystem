"""CliCI class for controlling all CLI functions."""
from __future__ import annotations


from pathlib import Path

from ecosystem.daos import DAO
from ecosystem.utils import parse_submission_issue
from ecosystem.utils.utils import set_actions_output


class CliCI:
    """CliCI class.
    Entrypoint for all CLI CI commands.

    Each public method of this class is CLI command
    and arguments for method are options/flags for this command.

    Ex: `python manager.py ci parser_issue --body="<SOME_MARKDOWN>"`
    """

    @staticmethod
    def add_member_from_issue(body: str, *, resources_dir: str | None = None) -> None:
        """Parse an issue created from the issue template and add the member to the database

        Args:
            body: body of the created issue
            resources_dir: (For testing) Path to the working directory

        Returns:
            None (side effect is updating database and writing actions output)
        """

        resources_dir = Path(resources_dir or (Path.cwd() / "ecosystem/resources"))

        parsed_result = parse_submission_issue(body)
        DAO(path=resources_dir).write(parsed_result)
        set_actions_output([("SUBMISSION_NAME", parsed_result.name)])
