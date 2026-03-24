"""CliCI class for controlling all CLI functions."""

import sys
from pathlib import Path
from ruamel.yaml import YAML

from ecosystem.dao import DAO
from ecosystem.submission_parser import parse_submission_issue
from ecosystem.error_handling import set_actions_output
from ecosystem.labels import LabelsToml
from ecosystem.validation import validate_member


class CliCI:
    """CliCI class.
    Entrypoint for all CLI CI commands.

    Each public method of this class is CLI command
    and arguments for method are options/flags for this command.

    Ex: `python manager.py ci add_member_from_issue --body="<SOME_MARKDOWN>"`
    """

    @staticmethod
    def add_member_from_issue(
        body: str, *, number: int | None = None, resources_dir: str | None = None
    ) -> None:
        """Parse an issue created from the issue template and add the member to the database

        Args:
            body: body of the created issue
            number: issue number. optional.
            resources_dir: (For testing) Path to the working directory

        Returns:
            None (side effect is updating database and writing actions output)
        """

        resources_dir = Path(resources_dir or (Path.cwd() / "ecosystem" / "resources"))

        parsed_result = parse_submission_issue(body, number)
        DAO(path=resources_dir).write(parsed_result)
        set_actions_output([("SUBMISSION_NAME", parsed_result.name)])
        set_actions_output([("SUBMISSION_SHORT_UUID", parsed_result.short_uuid)])

    @staticmethod
    def update_issue_template(
        template_path: str, *, resources_dir: str | None = None
    ) -> None:
        """Updates the labels and categories in the issue template

        Args:
            template_path: Path to the issue template to update
            resources_dir: Path to the resources directory
        """

        labels_toml = LabelsToml(resources_dir=resources_dir)

        yaml = YAML()
        with open(template_path, "r") as yaml_file:
            data = yaml.load(yaml_file)

        for section in data["body"]:
            if "id" not in section:
                continue
            if section["id"] == "labels":
                section["attributes"]["options"] = labels_toml.label_names
            elif section["id"] == "category":
                section["attributes"]["options"] = [
                    "Select one..."
                ] + labels_toml.category_names

        with open(template_path, "w") as yaml_file:
            yaml.dump(data, yaml_file)

    @staticmethod
    def create_sections(member_id: str, *, resources_dir: str | None = None) -> None:
        """TODO

        Args:
            member_id: loads the file ../ecosystem/resources/*_<member_id>.toml

        Returns:
            None (side effect is updating database and writing actions output)
        """

        resources_dir = Path(resources_dir or (Path.cwd() / "ecosystem" / "resources"))

        dao = DAO(path=resources_dir)
        for member in dao.get_all(member_id):
            member.upsert_sections()
            dao.write(member)

    @staticmethod
    def fetch_new_member_data(
        member_id: str, *, resources_dir: str | None = None
    ) -> None:
        """TODO

        Args:
            member_id: loads the file ../ecosystem/resources/*_<member_id>.toml

        Returns:
            None (side effect is updating database and writing actions output)
        """

        resources_dir = Path(resources_dir or (Path.cwd() / "ecosystem" / "resources"))

        dao = DAO(path=resources_dir)
        for member in dao.get_all(member_id):
            member.update_data()
            dao.write(member)

    @staticmethod
    def validate_member(member_id: str, *, resources_dir: str | None = None) -> None:
        """TODO

        Args:
            member_id: loads the file ../ecosystem/resources/*_<member_id>.toml

        Returns:
            None (it has no side-effect)
        """

        resources_dir = Path(resources_dir or (Path.cwd() / "ecosystem" / "resources"))

        dao = DAO(path=resources_dir)
        for member in dao.get_all(member_id):
            report = validate_member(member, verbose_level="-v")
            if report.exitcode == 0:
                print(f"::notice::  {member.name} ({member.name_id}) ✅")
                if report.xfailed:
                    print(f"::group:: some expected fail ☑️")
                    for xfailed in report.xfailed:
                        print(f"::notice:: {xfailed.nodeid} - {xfailed.wasxfail}️")
                    print("::endgroup::")
            else:
                for test in report.failed:
                    if test.passed:
                        continue
                    print(
                        f"::error:: {member.name} ({member.name_id}) - "
                        f"{test.nodeid} failed ❌\n"
                    )
                    print(f"::group:: {test.longreprtext}")
                    print("::endgroup::")
                sys.exit(report.exitcode)
