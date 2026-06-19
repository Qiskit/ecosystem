# This code is part of Qiskit.
#
# (C) Copyright IBM 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Submission model."""

from dataclasses import dataclass
from typing import Optional

from pathlib import Path
import yaml

from .error_handling import EcosystemError
from .request import URL
from .issue_body import EcosystemIssueBody as IssueBody


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
    labels: list[str]
    interfaces: list[str]
    terms: bool
    maturity: str
    pattern_steps: list[str]
    source_url: URL
    home_url: URL
    docs_url: URL
    package_urls: list[URL]
    paper_url: URL
    skip: Optional[list[str]] = None

    def __post_init__(self):
        if len(self.name) > 50:
            raise EcosystemError("Name too long")
        if len(self.description) > 135:
            raise EcosystemError("Description too long")
        if len(self.labels) > 5:
            raise EcosystemError("Too many labels")
        if not self.terms:
            raise EcosystemError("terms needs to be True")

    @classmethod
    def from_issue_text(cls, issue_text):
        """Takes the body of an issue and creates a Submission object"""
        issue_template = yaml.load(
            Path(".github/ISSUE_TEMPLATE/01_submission.yml").read_text(),
            Loader=yaml.SafeLoader,
        )
        issue_body = IssueBody(issue_text, issue_template)
        raw_kwargs = issue_body.to_dict()
        kwargs = {}
        for k, v in raw_kwargs.items():
            if k == "additional_submission_notes":
                continue
            if v == "_No response_":
                v = None
            if k == "skip_checks":
                k = "skip"
            kwargs[k] = v
        return Submission(**kwargs)

    @property
    def is_ibm_maintained(self):
        """It this going to be displayed as IBM maintained?"""
        # if maintainer is IBMer, it is ibm maintained
        if self.contact_info and self.contact_info.endswith("ibm.com"):
            return True
        # if hosted in Qiskit GitHub organization, it is ibm maintained
        if (
            self.source_url.hostname == "github.com"
            and self.source_url.path.lower().startswith("/qiskit/")
        ):
            return True
        return False
