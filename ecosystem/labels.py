"""Handles the labels.toml file"""

from pathlib import Path

import tomllib


class LabelsToml:
    """handles labels.toml"""

    def __init__(self, toml_filename: str = None, resources_dir: str = None):

        resources_dir = Path(
            resources_dir or Path.joinpath(Path.cwd(), "ecosystem", "resources")
        )

        toml_filename = toml_filename or Path.joinpath(resources_dir, "labels.toml")

        with open(toml_filename, "rb") as f:
            data = tomllib.load(f)
        self._data = data

    @property
    def category_descriptions(self):
        return {c["name"]: c.get("description") for c in self._data["categories"]}

    @property
    def category_sections(self):
        return {c["name"]: c.get("section") for c in self._data["categories"]}

    @property
    def category_names(self):
        """List of categories, just the names"""
        return [c["name"] for c in self._data["categories"]]

    @property
    def label_descriptions(self):
        return {c["name"]: c.get("description") for c in self._data["labels"]}

    @property
    def label_sections(self):
        return {c["name"]: c.get("section") for c in self._data["labels"]}

    @property
    def label_names(self):
        """List of labels, just the names"""
        return [c["name"] for c in self._data["labels"]]

    @property
    def interface_descriptions(self):
        return {c["name"]: c.get("description") for c in self._data["interfaces"]}

    @property
    def interface_sections(self):
        return {c["name"]: c.get("section") for c in self._data["interfaces"]}

    @property
    def interface_names(self):
        """List of intefaces, just the names"""
        return [c["name"] for c in self._data["interfaces"]]
