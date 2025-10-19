"""Submission model."""

from __future__ import annotations

import pprint
from datetime import datetime
from dataclasses import dataclass
from uuid import uuid4

from .utils import JsonSerializable, new_list


@dataclass
class Submission(JsonSerializable):
    """Main repository class.

    NOTE: These attribute names must correspond to field IDs in the issue
    template (.github/ISSUE_TEMPLATE/submission.yml).
    """

    # pylint: disable=too-many-instance-attributes
    name: str | None = None
    url: str | None = None
    description: str | None = None
    licence: str | None = None
    contact_info: str | None = None
    alternatives: str | None = None
    affiliations: str | None = None
    labels: list[str] = new_list()
    ibm_maintained: bool = False
    created_at: int | None = None
    updated_at: int | None = None
    website: str | None = None
    stars: int | None = None
    group: str | None = None
    reference_paper: str | None = None
    documentation: str | None = None
    uuid: str | None = None

    def __post_init__(self):
        self.__dict__.setdefault("created_at", datetime.now().timestamp())
        self.__dict__.setdefault("updated_at", datetime.now().timestamp())
        if self.uuid is None:
            self.uuid = str(uuid4())

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Transform dictionary to Submission.

        Args:
            dictionary: dict object

        Return: Submission
        """
        return Submission(**dictionary)

    def __eq__(self, other: "Submission"):
        return (
            self.url == other.url
            and self.description == other.description
            and self.licence == other.licence
        )

    def __repr__(self):
        return pprint.pformat(self.to_dict(), indent=4)

    def __str__(self):
        return f"Submission({self.name} | {self.url})"

    @property
    def name_id(self):
        """
        A unique and human-readable way to identify a submission
        It is used to create the TOML file name
        """
        # TODO: it is not uniq tho. Maybe add a random number at the end?  pylint: disable=W0511
        return self.url.strip("/").split("/")[-1]
