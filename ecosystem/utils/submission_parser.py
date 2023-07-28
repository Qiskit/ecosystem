"""Parser for issue submission."""
from collections import defaultdict
import mdformat

from ecosystem.models.repository import Repository


def _clean_section(section: str) -> {str: str}:
    """For a section, return a tuple with a title and "clean section".
    A clean section is without new lines and strip spaces"""
    paragraphs = section.split("\n")
    section = (" ").join(
        [paragraph.strip() for paragraph in paragraphs[1:] if paragraph]
    )
    title = paragraphs[0].strip()
    return (title, section)


def parse_submission_issue(body_of_issue: str) -> Repository:
    """Parse issue body.

    Args:
        body_of_issue: body of an GitHub issue in markdown

    Return: Repository
    """

    issue_formatted = mdformat.text(body_of_issue)

    sections = defaultdict(
        None, [_clean_section(s) for s in issue_formatted.split("### ")[1:]]
    )

    repo_name = sections["Github repo"].split("/")[-1]

    name = repo_name
    url = sections["Github repo"]
    description = sections["Description"]
    contact_info = sections["Email"]
    alternatives = sections["Alternatives"]
    licence = sections["License"]
    affiliations = sections["Affiliations"]
    website = sections["Website"]
    if website == "_No response_":
        website = None

    labels = [l.strip() for l in sections["Tags"].split(",")]
    if labels == ["_No response_"]:
        labels = []

    return Repository(
        name=name,
        url=url,
        description=description,
        licence=licence,
        contact_info=contact_info,
        alternatives=alternatives,
        affiliations=affiliations,
        labels=labels,
        website=website,
    )
