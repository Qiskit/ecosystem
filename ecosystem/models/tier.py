"""Tier of ecosystem membership."""
from __future__ import annotations

# pylint: disable=too-few-public-methods
class Tier:
    """Tiers of ecosystem membership."""

    MAIN: str = "Main"
    COMMUNITY: str = "Community"
    EXTENSION: str = "Extensions"

    @classmethod
    def all(cls) -> list[str]:
        """Returns all Tiers."""
        return [
            Tier.MAIN,
            Tier.COMMUNITY,
            Tier.EXTENSION,
        ]

    @classmethod
    def non_main_tiers(cls) -> list[str]:
        """Return all non Main tiers."""
        return [
            Tier.COMMUNITY,
            Tier.EXTENSION,
        ]
