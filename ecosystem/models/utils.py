"""Utility classes for models."""
from abc import ABC
from dataclasses import field


UnknownPackageVersion: str = "unknown"
new_list = lambda: field(default_factory=list)


class JsonSerializable(ABC):
    """Classes that can be serialized as json."""

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Converts dict to object.

        Args:
            dictionary: dict to convert
        """

    def to_dict(self) -> dict:
        """Converts repo to dict."""
        result = {}
        for key, val in self.__dict__.items():
            if key.startswith("_"):
                continue
            element = []
            if val is None:
                continue
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, JsonSerializable):
                        element.append(item.to_dict())
                    else:
                        element.append(item)
            elif isinstance(val, JsonSerializable):
                element = val.to_dict()
            else:
                element = val
            result[key] = element
        return result
