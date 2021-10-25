"""Parser for issue submission."""
import re
from ttp import ttp
import json

from ecosystem.models.repository import Repository


def parse_submission_issue(body_of_issue: str) -> Repository:
    """Parse issue body."""

    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(
        "{}/../templates/issue.md".format(current_dir), "r"
    ) as issue_body_tpl:
        issue_template = issue_body_tpl.read()

    parser = ttp(data=body_of_issue, template=issue_template)
    parser.parse()
    parser.result(format='json')[0]
    
    parse_json = json.loads(result)

    repo_name = parse_json[0]['repo_url'].split("/")

    name = repo_name[-1]
    url = parse_json[0]['repo_url']
    description = parse_json[0]['description']
    contact_info = parse_json[0]['email']
    alternatives = parse_json[0]['alternatives']
    license = parse_json[0]['license']
    affiliations = parse_json[0]['affiliations']

    labels = re.findall(r"([\w\]+)([\w\-\_]+)", parse_json[0]['tags'])

    return Repository(
        name,
        url,
        description,
        license,
        contact_info,
        alternatives,
        affiliations,
        labels,
    )
