"""Handles the /resources/classifications.toml file"""

from pathlib import Path

import tomllib


class ClassificationsToml:
    """handles /resources/classifications.toml"""

    def __init__(self, toml_filename: str = None, resources_dir: str = None):

        resources_dir = Path(resources_dir or Path.joinpath(Path.cwd(), "resources"))

        toml_filename = toml_filename or Path.joinpath(
            resources_dir, "classifications.toml"
        )

        with open(toml_filename, "rb") as f:
            data = tomllib.load(f)
        self._data = data

    @property
    def category_descriptions(self):
        """Returns dict category_name -> description"""
        return {c["name"]: c.get("description") for c in self._data["categories"]}

    @property
    def category_sections(self):
        """Returns dict category_name -> section"""
        return {c["name"]: c.get("section") for c in self._data["categories"]}

    @property
    def category_names(self):
        """List of categories, just the names"""
        return [c["name"] for c in self._data["categories"]]

    @property
    def label_descriptions(self):
        """Returns dict label_name -> description"""
        return {c["name"]: c.get("description") for c in self._data["labels"]}

    @property
    def label_sections(self):
        """Returns dict label_name -> section"""
        return {c["name"]: c.get("section") for c in self._data["labels"]}

    @property
    def label_names(self):
        """List of labels, just the names"""
        return [c["name"] for c in self._data["labels"]]

    @property
    def interface_descriptions(self):
        """Returns dict interface_name -> description"""
        return {c["name"]: c.get("description") for c in self._data["interfaces"]}

    @property
    def interface_sections(self):
        """Returns dict interface_name -> section"""
        return {c["name"]: c.get("section") for c in self._data["interfaces"]}

    @property
    def interface_names(self):
        """List of intefaces, just the names"""
        return [c["name"] for c in self._data["interfaces"]]
