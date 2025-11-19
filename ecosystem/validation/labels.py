"""Validations involving ecosystem/resources/labels.toml"""

from os import path
from pathlib import Path
import tomllib

from .base import MemberValidator


class Valid_TOML_Labels(
    MemberValidator
):  # pylint: disable=invalid-name, abstract-method)
    """Base class that loads ecosystem/resources/labels.toml"""

    def __init__(self):
        super().__init__()
        dir_path = path.dirname(path.realpath(__file__))
        labels_toml = path.abspath(Path(dir_path, "..", "resources", "labels.toml"))
        with open(labels_toml, "rb") as f:
            data = tomllib.load(f)
        self.categories = [c["name"] for c in data["categories"]]
        self.labels = [c["name"] for c in data["labels"]]


class ValidCategory(Valid_TOML_Labels):
    """member.group should exist in labels.toml"""

    def test(self):
        self.assertIn(
            self.member.group,
            self.categories,
            "{}: '{}' is not a valid category",
            self.member.name_id,
            self.member.group,
        )


class ValidLabel(Valid_TOML_Labels):
    """member.labels should exist in labels.toml"""

    def test(self):
        self.assertSubset(self.member.labels, self.labels)
