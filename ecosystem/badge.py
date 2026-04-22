"""Badge section."""

from dataclasses import dataclass
from typing import Optional

from .serializable import JsonSerializable
from .request import URL


@dataclass
class BadgeData(JsonSerializable):
    """
    The Badge data related to a project, based on
    https://img.shields.io/badges/endpoint-badge
    """

    url: str | URL  # the bitly link to the badge
    style: Optional[str] = None  # default: "flat"
    endpoint: Optional[str | URL] = None
    schemaVersion: Optional[int] = None
    label: Optional[str] = None
    message: Optional[str] = None
    color: Optional[str] = None
    labelColor: Optional[str] = None
    isError: Optional[str] = None
    logoColor: Optional[str] = None
    logoSize: Optional[str] = None

    def __post_init__(self):
        self.url = self.url if isinstance(self.url, URL) else URL(self.url)
        self.style = "flat" if self.style is None else str(self.style)
