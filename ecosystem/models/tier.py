"""Tier of ecosystem membership."""


# pylint: disable=too-few-public-methods
from typing import List


class Tier:
    """Tiers of ecosystem membership."""

    MAIN: str = "Main"
    COMMUNITY: str = "Community"
    EXTENSION: str = "Extensions"

    @classmethod
    def all(cls) -> List[str]:
        """Returns all Tiers."""
        return [
            Tier.MAIN,
            Tier.COMMUNITY,
            Tier.EXTENSION,
        ]

    @classmethod
    def non_main_tiers(cls) -> List[str]:
        """Return all non Main tiers."""
        return [
            Tier.COMMUNITY,
            Tier.EXTENSION,
        ]
