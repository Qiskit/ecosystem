import tomllib
from os import path
from pathlib import Path


class MemberValidator:
    def __init__(self):
        self.valid = False
        self.reason = None

    def validate(self, member): ...


class ValidCategory(MemberValidator):
    def __init__(self):
        dir_path = path.dirname(path.realpath(__file__))
        labels_toml = path.abspath(Path(dir_path, "..", "resources", "labels.toml"))
        with open(labels_toml, "rb") as f:
            data = tomllib.load(f)
        self.categories = [c["name"] for c in data["categories"]]

    def validate(self, member):
        if member.group in self.categories:
            self.valid = True
        else:
            self.reason = f"'{member.group}' is not a valid category"
            self.valid = False
        return self.valid
