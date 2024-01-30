"""Repository model."""
from __future__ import annotations

import pprint
from datetime import datetime
from dataclasses import dataclass

from .tier import Tier
from .utils import JsonSerializable, new_list


@dataclass
class Repository(JsonSerializable):
    """Main repository class."""

    # pylint: disable=too-many-instance-attributes
    name: str
    url: str
    description: str
    licence: str
    contact_info: str | None = None
    alternatives: str | None = None
    affiliations: str | None = None
    labels: list[str] = new_list()
    created_at: int | None = None
    updated_at: int | None = None
    tier: str = Tier.COMMUNITY
    website: str | None = None
    stars: int | None = None
    group: str | None = None
    reference_paper: str | None = None
    documentation: str | None = None

    def __post_init__(self):
        self.__dict__.setdefault("created_at", datetime.now().timestamp())
        self.__dict__.setdefault("updated_at", datetime.now().timestamp())

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Transform dictionary to Repository.

        Args:
            dictionary: dict object

        Return: Repository
        """
        return Repository(**dictionary)

    def __eq__(self, other: "Repository"):
        return (
            self.tier == other.tier
            and self.url == other.url
            and self.description == other.description
            and self.licence == other.licence
        )

    def __repr__(self):
        return pprint.pformat(self.to_dict(), indent=4)

    def __str__(self):
        return f"Repository({self.tier} | {self.name} | {self.url})"
