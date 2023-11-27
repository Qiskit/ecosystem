"""CliWebsite class for controlling all CLI functions."""
import os
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from ecosystem.daos import DAO


class CliWebsite:
    """CliMembers class.
    Entrypoint for all CLI website commands.

    Each public method of this class is CLI command
    and arguments for method are options/flags for this command.

    Ex: `python manager.py website build_website`
    """

    def __init__(self, root_path: Optional[str] = None):
        """CliWebsite class."""
        self.current_dir = root_path or os.path.abspath(os.getcwd())
        self.resources_dir = "{}/ecosystem/resources".format(self.current_dir)
        self.dao = DAO(path=self.resources_dir)

    def build_website(self):
        """Generates the ecosystem web page reading `members.json`."""
        environment = Environment(loader=FileSystemLoader("ecosystem/html_templates/"))
        projects = self.dao.storage.read()
        projects_sorted = sorted(
            projects.items(),
            key=lambda item: (
                -item[1].stars if item[1].stars is not None else 0,
                item[1].name,
            ),
        )
        templates = {
            "website": environment.get_template("webpage.html.jinja"),
            "card": environment.get_template("card.html.jinja"),
            "tag": environment.get_template("tag.html.jinja"),
            "link": environment.get_template("link.html.jinja"),
        }
        sections = {
            "transpiler_plugin": "",
            "provider": "",
            "applications": "",
            "other": "",
        }

        max_chars_description_visible = 400
        min_chars_description_hidden = 100
        count_read_more = 1
        for _, repo in projects_sorted:
            # Card tags
            tags = ""
            for label in repo.labels:
                tags += templates["tag"].render(color="purple", title=label, text=label)

            # Card links
            links = templates["link"].render(url=repo.url, place="repository")
            if repo.website:
                links += templates["link"].render(url=repo.website, place="website")

            # Card description
            if (
                len(repo.description) - max_chars_description_visible
                >= min_chars_description_hidden
            ):
                description = [
                    repo.description[:max_chars_description_visible],
                    repo.description[max_chars_description_visible:],
                ]
                id_read_more = str(count_read_more)
                count_read_more += 1
            else:
                description = [repo.description, ""]
                id_read_more = "None"

            # Create the card
            card = templates["card"].render(
                title=repo.name,
                tags=tags,
                description_visible=description[0],
                description_hidden=description[1],
                id_read_more=id_read_more,
                links=links,
            )

            # Adding the card to a section
            sections[repo.group] += card

        return templates["website"].render(
            section_transpiler_plugin_cards=sections["transpiler_plugin"],
            section_provider_cards=sections["provider"],
            section_applications_cards=sections["applications"],
            section_other_cards=sections["other"],
        )
