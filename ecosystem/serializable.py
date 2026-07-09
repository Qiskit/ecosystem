# This code is part of Qiskit.
#
# (C) Copyright IBM 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Utility classes for models."""

from abc import ABC
from datetime import date

from ecosystem.license import License
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

    def to_dict(self, keys=None) -> dict:  # pylint: disable=too-many-branches
        """Converts Object to dict.
        if keys = None, then takes `self.__dict__.keys()`. Otherwise, this is a list of keys.
        """
        if keys is None:
            keys = self.__dict__.keys()
        result = {}
        for key in keys:
            val = getattr(self, key, None)
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
            elif isinstance(val, (URL, License)):
                element = str(val)
            else:
                element = val
            result[key] = element
        return result


def parse_date(date_str):
    """Normalize dates to datetime.date ISO format.
    If date_str is "now" or "today", then makes a date with today."""
    if date_str is None:
        return None
    if isinstance(date_str, date):
        return date_str
    if date_str in ["now", "today"]:
        return date.today()
    return date.fromisoformat(date_str[:10])
