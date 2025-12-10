"""Parser for issue submission."""

import mdformat

from .submission import Submission
from .member import Member


def parse_submission_issue(body_of_issue: str) -> Member:
    """Parse issue body.

    The GitHub issue is a collection of "fields", each of which has a
    "label" and an "ID" specified in the template. We require IDs in the
    template to match argument names of the Submission model.

    We receive issues as a markdown string. The markdown contains a section for
    each field; the heading of a section is the "label", and the content that
    follows it is the information the user submitted for that field.

    ```
    ### Field label

    Content user has submitted for that field.
    ```

    This function parses the markdown to create a dict of { label: content },
    then, using the issue template, transforms labels to IDs to create a
    dictionary { id: content }. Since the IDs match arguments of the Submission
    constructor, this dict is the "args" needed to create the Submission object.

    Since users can only submit strings, we map the string "_No response_" to
    None and parse the "labels" field into a list.

    Args:
        body_of_issue: body of an GitHub issue in markdown

    Return: Member
    """

    issue_formatted = mdformat.text(body_of_issue)

    submission = Submission.from_formatted_issue(issue_formatted)
    # TODO: validate submission. # pylint: disable=fixme
    return Member.from_submission(submission)
