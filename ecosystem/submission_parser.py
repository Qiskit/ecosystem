"""Parser for issue submission."""

from pathlib import Path
from urllib.parse import urlparse
import mdformat
import yaml

from ecosystem.submission import Submission


def _parse_section(section: str, label_to_id: dict[str, str]) -> tuple[str, str]:
    """For a section, return its field ID and the content.
    The content has no newlines and has spaces stripped.
    """
    lines = section.split("\n")
    content = " ".join(line.strip() for line in lines[1:] if line)
    label = lines[0].strip()
    field_id = label_to_id[label]
    return field_id, content


def _get_label_to_id_map() -> dict[str, str]:
    """Create a dict that maps a fields "label" to its `id` from the issue
    template
    """
    issue_template = yaml.load(
        Path(".github/ISSUE_TEMPLATE/submission.yml").read_text(),
        Loader=yaml.SafeLoader,
    )
    label_to_id = {
        form["attributes"]["label"]: form["id"]
        for form in issue_template["body"]
        if form["type"] != "markdown"
    }
    return label_to_id


def parse_submission_issue(body_of_issue: str) -> Submission:
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

    Return: Submission
    """

    issue_formatted = mdformat.text(body_of_issue)

    md_sections = issue_formatted.split("### ")[1:]
    label_to_id = _get_label_to_id_map()
    args = dict(_parse_section(s, label_to_id) for s in md_sections)

    args = {
        field_id: (None if content == "_No response_" else content)
        for field_id, content in args.items()
    }

    if args["labels"] is None:
        args["labels"] = []
    else:
        args["labels"] = [x.strip() for x in args["labels"].split(",")]
    url = urlparse(args["url"])

    if args["contact_info"].endswith("ibm.com"):
        # if hosted in maintainer is IBMer, it is ibm maintained
        args["ibm_maintained"] = True
    elif url.hostname == "github.com" and url.path.lower().startswith("/qiskit/"):
        # if hosted in Qiskit GitHub organization, it is ibm maintained
        args["ibm_maintained"] = True
    else:
        args["ibm_maintained"] = False

    return Submission.from_dict(args)
