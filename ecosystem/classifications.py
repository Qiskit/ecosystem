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

    def __getattr__(self, attr):
        """
        - <classification>_names: List of the name of a particular classificaiton
        - <classification>_descriptions: Dict <classificaiton>_name -> description
        """
        if attr.endswith("_names"):
            classification = attr[: -len("_names")]
            return [c["name"] for c in self._data[classification]]
        elif attr.endswith("_descriptions"):
            classification = attr[: -len("_descriptions")]
            return {c["name"]: c.get("description") for c in self._data[classification]}
        elif attr.endswith("_sections"):
            classification = attr[: -len("_sections")]
            return {c["name"]: c.get("section") for c in self._data[classification]}
        raise AttributeError(attr)

    @property
    def category_sections(self):
        """Returns dict category_name -> section"""
        return {c["name"]: c.get("section") for c in self._data["categories"]}

    @property
    def label_sections(self):
        """Returns dict label_name -> section"""
        return {c["name"]: c.get("section") for c in self._data["labels"]}

    @property
    def interface_sections(self):
        """Returns dict interface_name -> section"""
        return {c["name"]: c.get("section") for c in self._data["interfaces"]}
