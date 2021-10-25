"""Parser for issue submission."""
import re

from ecosystem.models.repository import Repository


def parse_submission_issue(body_of_issue: str) -> Repository:
    """Parse issue body."""
    
    issue_formatted = mdformat.text(body_of_issue)
    
    parse = re.findall(r"^([\s\S]*?)(?:\n{2,}|\Z)", body_of_issue, re.M)

    repo_name = parse[1].split("/")

    name = repo_name[-1]
    url = parse[1]
    description = parse[3]
    contact_info = parse[5]
    alternatives = parse[7]
    licence = parse[9]
    affiliations = parse[11]

    labels = re.findall(r"([\w\]+)([\w\-\_]+)", parse[13])

    return Repository(
        name,
        url,
        description,
        licence,
        contact_info,
        alternatives,
        affiliations,
        labels,
    )
