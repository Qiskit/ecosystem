"""Classes and controllers for json storage."""
import inspect
from abc import ABC
from datetime import datetime
from typing import Optional, List


# pylint: disable=too-few-public-methods
class Tier:
    """Tiers of ecosystem membership."""
    MAIN: str = "MAIN"
    MEMBER: str = "MEMBER"
    CANDIDATE: str = "CANDIDATE"


class Repository(ABC):
    """Main repository class."""

    tier: str

    def __init__(self,
                 name: str,
                 url: str,
                 description: str,
                 licence: str,
                 contact_info: Optional[str] = None,
                 alternatives: Optional[str] = None,
                 labels: Optional[List[str]] = None,
                 created_at: Optional[int] = None,
                 updated_at: Optional[int] = None,
                 tier: Optional[str] = None):
        """Repository controller.

        Args:
            name: name of project
            url: url to github repo
            description: description
            licence: licence
            contact_info: contact information
            alternatives: alternatives to project
            labels: labels
            created_at: creation date
            updated_at: update date
        """
        self.name = name
        self.url = url
        self.description = description
        self.licence = licence
        self.contact_info = contact_info
        self.alternatives = alternatives
        self.labels = labels if labels is not None else []
        self.created_at = created_at if created_at is not None else datetime.now().timestamp()
        self.updated_at = updated_at if updated_at is not None else datetime.now().timestamp()
        if tier:
            self.tier = tier

    def to_dict(self) -> dict:
        """Converts repo to dict."""
        result = dict()
        for name, value in inspect.getmembers(self):
            if not name.startswith('_') and \
                    not inspect.ismethod(value) and not inspect.isfunction(value) and \
                    hasattr(self, name):
                result[name] = value
        return result

    def __eq__(self, other: 'Repository'):
        return (self.tier == other.tier
                and self.url == other.url
                and self.description == other.description
                and self.licence == other.licence)


class MainRepository(Repository):
    """Main tier repository."""
    tier = Tier.MAIN
