"""Utility classes for models."""

from abc import ABC
from datetime import date

from ecosystem.request import URL


class JsonSerializable(ABC):
    """Classes that can be serialized as json."""

    def __str__(self):
        return str(self.to_dict())

    def __eq__(self, other):
        if not hasattr(other, "to_dict"):
            return False
        return self.to_dict() == other.to_dict()

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Converts dict to object.

        Args:
            dictionary: dict to convert
        """
        return cls(**dictionary)

    def to_dict(self) -> dict:  # pylint: disable=too-many-branches
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
                    elif isinstance(item, URL):
                        element.append(str(item))
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
            elif isinstance(val, URL):
                element = str(val)
            else:
                element = val
            result[key] = element
        return result


def parse_datetime(date_str):
    """Normalize the datetime.date format from ISO format.
    If date_str is "now" or "today", then makes a date with now."""
    if date_str in ["now", "today"]:
        _date = date.today()
    else:
        _date = date.fromisoformat(date_str[:10])
    return _date.replace(microsecond=0)
