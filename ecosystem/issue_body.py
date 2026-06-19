# This code is part of Qiskit.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Object to handle the body of an issue issue submission."""

import mdformat
from slugify import slugify

from .request import URL
from .error_handling import EcosystemError, logger


class IssueBody:
    """Helper and formatter for the issue body based on an issue template"""

    def __init__(self, issue_body: str, template_yaml):
        """
        Process an issue body
        Args:
            issue_body: Body text of the issue in the format
                ### header 1

                body 1
            template_yaml: The output of ``yaml.load``

        """
        self.issue_formatted = mdformat.text(issue_body)
        self.sections = {}
        self.template_yaml = template_yaml
        self._label_to_id = None
        md_sections = self.issue_formatted.split("### ")[1:]

        for section in md_sections:
            lines = [line.strip() for line in section.split("\n") if line.strip()]
            key = lines[0]
            value = "\n".join(lines[1:])
            self.sections[key] = value

    def to_dict(self):
        """Parses each section in self.sections and creates a dict.
        The values are the result of "process_" methods.
        """
        return dict(self._parse_sections())

    @property
    def label_to_id(self) -> dict[str, str]:
        """Create a two-ways dict that maps a fields "label" and "id" with some extra information
        - "id"
        - "label"
        - "type"
        - "required"
        """
        if self._label_to_id is None:
            self._label_to_id = {}
            for form in self.template_yaml["body"]:
                section = {}
                if form["type"] == "markdown":
                    continue
                section["id"] = form.get("id")
                section["label"] = form.get("attributes", {}).get("label")
                section["required"] = form.get("validations", {}).get("required")
                section["type"] = form.get("type")
                section["multiple"] = form.get("attributes", {}).get("multiple", False)

                if section["id"].endswith("_url"):
                    section["type"] = "url"

                if section["type"] == "dropdown":
                    section["type"] += "_multiple" if section["multiple"] else "_single"

                if hasattr(self, f'process_type_{section["type"]}'):
                    section["handler"] = getattr(
                        self, f'process_type_{section["type"]}'
                    )
                self._label_to_id[section["label"]] = section
        return self._label_to_id

    def _parse_sections(self):
        """For each section in self.sections, yields its field ID and the content.
        The content has no newlines and has spaces stripped.
        """
        for section, content in self.sections.items():

            if section not in self.label_to_id:
                template_id = slugify(section, separator="_")
                template = {}
                logger.warning(
                    "Section %s not found in template. Converting it to %s",
                    section,
                    template_id,
                )
            else:
                template = self.label_to_id[section]
                template_id = template["id"]

            if hasattr(self, f"process_{template_id}"):
                yield (
                    template_id,
                    getattr(self, f"process_{slugify(template_id, separator='_')}")(
                        content
                    ),
                )
            elif "handler" in template:
                yield (template_id, template["handler"](content))
            else:
                yield (template_id, str(content).strip())

    @staticmethod
    def process_type_url(content) -> URL:
        """Creates a URL based on the content. If content == "_No response_" then returns None"""
        try:
            if content and content != "_No response_":
                return URL(content)
            return None
        except EcosystemError:
            return None

    @staticmethod
    def process_type_dropdown_multiple(content) -> list[str]:
        """Split the content into a list, ignoring the items starting with "_" """
        return [i.strip() for i in content.split(",") if not i.strip().startswith("_")]

    @staticmethod
    def process_type_dropdown_single(content) -> str:
        """A selected option for a dropdown without multiple selection"""
        return content.strip()

    @staticmethod
    def process_type_checkboxes(content):
        """Checkboxes that are checked, start with '- [x]'"""
        return content.strip().startswith("- [x]")


class EcosystemIssueBody(IssueBody):
    """Specific implementation of IssueBody for ecosystem issues"""

    @staticmethod
    def process_package_urls(content) -> list[URL]:
        """The package_urls section is a markdown codeblock with a list of URLs"""
        lines = [i.strip() for i in content.split("\n")][1:-1]
        return [IssueBody.process_type_url(pkg) for pkg in lines]

    @staticmethod
    def process_description(content) -> str:
        """A description might (or not) be a markdown codeblock"""
        lines = [i.strip() for i in content.split("\n")]
        if lines and lines[0].startswith("```"):
            return "\n".join(lines[1:-1])
        return "\n".join(lines)

    @staticmethod
    def process_skip_checks(content) -> list[list[str]]:
        """
        Return a list of (id, description) tuples
            ### skip checks

            COC: This project does not need to agree the CoC
            010: This project is allow to have "test" in its name
        """
        lines = [i.strip() for i in content.split("\n")]
        return [l.split(": ") for l in lines if ":" in l]
