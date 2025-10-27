"""Utility classes for models."""

from abc import ABC
from collections import namedtuple
from functools import reduce


# key to write in the member toml and how to fetch it from the json file and how to reduce it
Alias = namedtuple("Alias", ["jsonpath", "reduceFunc"])

class JsonSerializable(ABC):
    """Classes that can be serialized as json."""

    def __str__(self):
        return str(self.to_dict())

    def __eq__(self, other):
        return self.to_dict() == other.to_dict()

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Converts dict to object.

        Args:
            dictionary: dict to convert
        """
        return cls(**dictionary)

    def to_dict(self) -> dict:
        """Converts Object to dict."""
        result = {}
        for key, val in self.__dict__.items():
            if key.startswith("_") or val is None:
                continue
            if isinstance(val, list):
                element = []
                for item in val:
                    if isinstance(item, JsonSerializable):
                        element.append(item.to_dict())
                    else:
                        element.append(item)
            elif isinstance(val, dict):
                dict_element = {}
                for k, v in val.items():
                    dict_element[k] = v.to_dict() if hasattr(v, "to_dict") else v
                if dict_element:
                    element = dict_element
                else:
                    continue
            elif isinstance(val, JsonSerializable):
                element = val.to_dict()
            else:
                element = val
            result[key] = element
        return result
