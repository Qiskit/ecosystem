"""Tier of ecosystem membership."""


# pylint: disable=too-few-public-methods
from typing import List


class Tier:
    """Tiers of ecosystem membership."""

    MAIN: str = "Main"
    COMMUNITY: str = "Community"
    PROTOTYPES: str = "Prototypes"
    PARTNERS: str = "Partners"
    EXTENSION: str = "Extension"

    @classmethod
    def all(cls) -> List[str]:
        """Returns all Tiers."""
        return [
            Tier.MAIN,
            Tier.COMMUNITY,
            Tier.PROTOTYPES,
            Tier.PARTNERS,
            Tier.EXTENSION,
        ]

    @classmethod
    def non_main_tiers(cls) -> List[str]:
        """Return all non Main tiers."""
        return [
            Tier.COMMUNITY,
            Tier.PROTOTYPES,
            Tier.PARTNERS,
            Tier.EXTENSION,
        ]
