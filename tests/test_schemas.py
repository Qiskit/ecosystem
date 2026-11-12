# This code is part of Qiskit.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""Tests for the JSON schemas in resources/"""

import json
from datetime import date, datetime, time
from pathlib import Path
from unittest import TestCase

import tomllib
from jsonschema import Draft202012Validator, FormatChecker

from ecosystem.classifications import ClassificationsToml
from ecosystem.member import Member


def toml_to_json(value):
    """Make a parsed TOML value comparable to the schema.

    TOML has native date, datetime and time types, and the schema calls those fields
    `"type": "string"` with `"format": "date"`. `taplo check` (what CI runs) reads
    them as strings, so this does the same instead of loosening the schema.
    """
    if isinstance(value, dict):
        return {key: toml_to_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [toml_to_json(item) for item in value]
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    return value


class MembersSchemaTestCase(TestCase):
    """The enums in resources/members-schema.json and the classifications should not drift"""

    def setUp(self) -> None:
        self.resources_dir = Path(__file__).parent.parent / "resources"
        with open(self.resources_dir / "members-schema.json") as schema_file:
            self.schema = json.load(schema_file)
        self.classifications = ClassificationsToml(resources_dir=self.resources_dir)

    def test_maturity_enum(self):
        """member.maturity accepts every maturity level in classifications.toml"""
        self.assertEqual(
            self.schema["properties"]["maturity"]["enum"],
            self.classifications.maturity_names,
        )

    def test_status_enum(self):
        """member.status accepts every status in classifications.toml.
        "Member" is the default status, but it can also be explicit in a member file"""
        self.assertEqual(
            self.schema["properties"]["status"]["enum"],
            self.classifications.status_names,
        )

    def test_the_schema_itself_is_valid(self):
        """An invalid schema validates nothing, and does it silently.

        `labels` and `interfaces` used to declare `"items": [{"type": "string"}]`, the
        draft-4 array form, which is not valid `items` in the draft 2020-12 this file
        declares. `jsonschema` rejected the whole schema over it, and `taplo check`
        dropped the constraint rather than failing, so `labels = ["ok", 42]` passed.
        """
        Draft202012Validator.check_schema(self.schema)


class MemberFilesTestCase(TestCase):
    """Every file in resources/members validates against resources/members-schema.json.

    CI checks this with `taplo check --schema` (see .github/workflows/tests.yml), which
    only looks at the files as committed. Running it here as well means a member built
    in code -- by a submission, or by one of the `manager.py members update_*` commands
    -- can be checked against the schema before it is written.
    """

    def setUp(self) -> None:
        self.resources_dir = Path(__file__).parent.parent / "resources"
        with open(self.resources_dir / "members-schema.json") as schema_file:
            schema = json.load(schema_file)
        self.validator = Draft202012Validator(schema, format_checker=FormatChecker())
        self.member_files = sorted((self.resources_dir / "members").glob("*.toml"))

    def test_there_are_member_files_to_check(self):
        """Guard against the glob silently finding nothing"""
        self.assertTrue(self.member_files)

    def test_every_member_file_validates(self):
        """Each member file is a valid member"""
        for path in self.member_files:
            with self.subTest(member=path.name):
                member = toml_to_json(tomllib.loads(path.read_text()))
                errors = sorted(
                    self.validator.iter_errors(member), key=lambda e: list(e.path)
                )
                messages = [
                    f"{'.'.join(str(part) for part in error.path) or '<root>'}: "
                    f"{error.message}"
                    for error in errors
                ]
                self.assertFalse(messages, f"{path.name}\n" + "\n".join(messages))

    def test_every_member_has_an_address(self):
        """A member says where the project lives, one way or the other.

        `url` is no longer a required key, because `Member.url` derives it from `[github]`
        and `upsert_sections` drops the stored copy once it has. Nothing in the schema
        asks for either half, so this is what is left to say a member has an address at
        all.
        """
        for path in self.member_files:
            with self.subTest(member=path.name):
                member = Member.from_dict(tomllib.loads(path.read_text()))
                self.assertIsNotNone(
                    member.url,
                    f"{path.name} carries no `url` and no `[github]` to derive one from",
                )

    def test_no_two_members_are_the_same_project(self):
        """One project is one member.

        Read through `Member.url`, not off the file: the address lives in `[github]` for
        every member that has one, so comparing the stored key would compare 220 blanks.
        A member that is one directory of a repository keeps its `/tree/<ref>/<path>`, so
        the templates of `qiskit-function-templates` stay distinct here.
        """
        members = {}
        for path in self.member_files:
            member = Member.from_dict(tomllib.loads(path.read_text()))
            url = str(member.url) if member.url else f"<no url: {path.name}>"
            members.setdefault(url.rstrip("/").casefold(), []).append(path.name)

        shared = {url: names for url, names in members.items() if len(names) > 1}
        self.assertFalse(
            shared,
            "\n".join(
                f"{url} is declared by {', '.join(sorted(names))}"
                for url, names in sorted(shared.items())
            ),
        )
