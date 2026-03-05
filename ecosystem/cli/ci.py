"""CliCI class for controlling all CLI functions."""

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

        member = parse_submission_issue(body, number)
        DAO(path=resources_dir).write(member)
        set_actions_output([("SUBMISSION_NAME", member.name)])
        set_actions_output([("SUBMISSION_SHORT_UUID", member.short_uuid)])

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
    def validate_new_member_yml(
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
            passing, not_passing = validate_member(member)
            if not passing:
                print(
                    f"::warning:: {member.name} ({member.name_id}) has no validations?"
                )
            if not not_passing:
                print(f"::notice:: {member.name} ({member.name_id}) passed ✅")
            for failing_validation in not_passing:
                print(
                    f"::error:: {member.name} ({member.name_id}) - "
                    f"{failing_validation.name} failed ❌: "
                    f"{failing_validation.class_obj.__doc__}"
                )
