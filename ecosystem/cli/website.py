"""CliWebsite class for controlling all CLI functions."""
from pathlib import Path
from typing import Optional
import json
import os
import toml

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
        resources_dir = Path(self.current_dir, "ecosystem/resources")
        self.dao = DAO(path=resources_dir)
        self.label_descriptions = {
            item["name"]: item["description"]
            for item in json.loads(Path(resources_dir, "labels.json").read_text())
        }
        self.web_data = toml.loads((resources_dir / "website.toml").read_text())

    def build_website(self):
        """Generates the ecosystem web page reading the TOML files."""
        # pylint: disable=too-many-locals
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
        sections = {group["id"]: group for group in self.web_data["groups"]}
        for section in sections.values():
            section.setdefault("html", "")

        max_chars_description_visible = 400
        min_chars_description_hidden = 100
        count_read_more = 1
        for _, repo in projects_sorted:
            # Card tags
            tags = ""
            for index, label in enumerate(repo.labels):
                tags += templates["tag"].render(
                    color="purple",
                    text=label,
                    tooltip=self.label_descriptions[label],
                    # Sometimes tooltips are clipped by the browser window.
                    # While not perfect, the following line solves 95% of cases
                    alignment="bottom" if (index % 3) == 2 else "bottom-left",
                )

            # Card links
            links = ""
            for url, link_text in (
                (repo.url, "repository"),
                (repo.website, "website"),
                (repo.reference_paper, "paper"),
                (repo.documentation, "documentation"),
            ):
                if url:
                    links += templates["link"].render(url=url, place=link_text)

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
            sections[repo.group]["html"] += card

        return templates["website"].render(
            header=self.web_data["header"],
            sections=sections.values(),
        )
