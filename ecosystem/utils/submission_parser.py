"""Parser for issue submission."""

from pathlib import Path
import mdformat
import yaml

from ecosystem.models.repository import Repository


def _parse_section(section: str) -> tuple[str, str]:
    """For a section, return its field ID and the content.
    The content has no newlines and has spaces stripped.
    """
    lines = section.split("\n")
    content = " ".join(line.strip() for line in lines[1:] if line)
    label = lines[0].strip()
    field_id = _label_to_id(label)
    return field_id, content


def _label_to_id(label: str) -> str:
    """Given a fields "label", find its `id` from the issue template"""
    if not hasattr(_label_to_id, "map"):
        # Store as attribute so we only need to read the template once
        issue_template = yaml.load(
            Path(".github/ISSUE_TEMPLATE/submission.yml").read_text(),
            Loader=yaml.SafeLoader,
        )
        _label_to_id.map = {
            form["attributes"]["label"]: form["id"]
            for form in issue_template["body"]
            if form["type"] != "markdown"
        }
    return _label_to_id.map[label]


def parse_submission_issue(body_of_issue: str) -> Repository:
    """Parse issue body.

    The GitHub issue is a collection of "fields", each of which has a
    "label" and an "ID" specified in the template. We require IDs in the
    template to match argument names of the Repository model.

    We recieve issues as a markdown string. The markdown contains a section for
    each field; the heading of a section is the "label", and the content that
    follows it is the information the user submitted for that field.

    ```
    ### Field label

    Content user has submitted for that field.
    ```

    This function parses the markdown to create a dict of { label: content },
    then, using the issue template, transforms labels to IDs to create a
    dictionary { id: content }. Since the IDs match arguments of the Repository
    constructor, this dict is the "args" needed to create the Repository object.

    Since users can only submit strings, we map the string "_No response_" to
    None and parse the "labels" field into a list.

    Args:
        body_of_issue: body of an GitHub issue in markdown

    Return: Repository
    """

    issue_formatted = mdformat.text(body_of_issue)

    md_sections = issue_formatted.split("### ")[1:]
    args = dict(_parse_section(s) for s in md_sections)

    args = {
        field_id: (None if content == "_No response_" else content)
        for field_id, content in args.items()
    }

    if args["labels"] is None:
        args["labels"] = []
    else:
        args["labels"] = [l.strip() for l in args["labels"].split(",")]

    return Repository(**args)
