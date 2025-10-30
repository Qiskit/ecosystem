"""Submission model."""

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import ParseResult
import yaml

from .request import parse_url


@dataclass
class Submission:
    """Submission class.

    NOTE: These attribute names must correspond to field IDs in the issue
    template (.github/ISSUE_TEMPLATE/01_submission.yml).
    """

    name: str
    description: str
    contact_info: str
    category: str
    labels: str
    terms: bool
    pattern_steps: str
    source_url: ParseResult
    home_url: ParseResult
    docs_url: ParseResult
    package_urls: list[ParseResult]
    paper_url: ParseResult

    @property
    def name_id(self):
        """
        A unique and human-readable way to identify a submission
        It is used to create the TOML file name
        """
        # TODO: it is not uniq tho. Maybe add a random number at the end?  pylint: disable=W0511
        return self.source_url.geturl().strip("/").split("/")[-1]

    @classmethod
    def from_formatted_issue(cls, issue_formatted):
        """Takes a formated issue and creates a Submission object"""
        md_sections = issue_formatted.split("### ")[1:]
        label_to_id = cls._labels_ids()
        kwargs = dict(cls._parse_section(s, label_to_id) for s in md_sections)
        return Submission(**kwargs)

    @classmethod
    def _labels_ids(cls) -> dict[str, str]:
        """Create a two-ways dict that maps a fields "label" and "id" with some extra information
        - "id"
        - "label"
        - "type"
        - "required"
        """
        issue_template = yaml.load(
            Path(".github/ISSUE_TEMPLATE/01_submission.yml").read_text(),
            Loader=yaml.SafeLoader,
        )
        label_to_id = {}
        for form in issue_template["body"]:
            section = {}
            if form["type"] == "markdown":
                continue
            section["id"] = form.get("id")
            section["label"] = form.get("attributes", {}).get("label")
            section["type"] = form.get("type")
            section["required"] = form.get("validations", {}).get("required")
            label_to_id[section["id"]] = section
            label_to_id[section["label"]] = section
        return label_to_id

    @staticmethod
    def _parse_section(section: str, label_to_id: dict[str, str]):
        """For a section, return its field ID and the content.
        The content has no newlines and has spaces stripped.
        """
        lines = [line.strip() for line in section.split("\n") if line.strip()]
        label = lines[0]
        field_id = label_to_id[label]["id"]
        field_type = label_to_id[label]["type"]

        if "textarea" == field_type and lines[1].startswith("```"):
            raw_content = lines[2:-1]
        else:
            raw_content = lines[1:]

        if "dropdown" == field_type and "category" != field_id:
            content = raw_content
        elif "checkboxes" == field_type:
            content = raw_content[0].startswith("- [x]")
        elif field_id.endswith("_url"):
            content = parse_url(raw_content[0]) if raw_content else None
        elif field_id.endswith("_urls"):
            content = [parse_url(url) for url in raw_content]
        else:
            content = " ".join(raw_content)
        return field_id, content

    @property
    def is_ibm_maintained(self):
        """It this going to be displayed as IBM maintained?"""
        # if maintainer is IBMer, it is ibm maintained
        if self.contact_info.endswith("ibm.com"):
            return True
        # if hosted in Qiskit GitHub organization, it is ibm maintained
        if (
            self.source_url.hostname == "github.com"
            and self.source_url.path.lower().startswith("/qiskit/")
        ):
            return True
        return False
