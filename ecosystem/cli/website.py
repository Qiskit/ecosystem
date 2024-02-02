"""CliWebsite class for controlling all CLI functions."""
from pathlib import Path
from typing import Optional
import json
import os
import toml

from jinja2 import Environment, FileSystemLoader

from ecosystem.daos import DAO

def build_website(resources: str, output: str):
    """
    Generates the ecosystem web page from data in `resources` dir, writing to `output` dir.
    """
    resources_dir = Path(resources)
    html = _build_html(*_load_from_file(resources_dir))
    with open(Path(output, "index.html"), "w") as f:
        f.write(html)

def _load_from_file(resources_dir: Path):
    """
    Loads:
        * Projects list
        * Website strings
        * Label descriptions
        * Jinja templates
    """
    # Projects list
    dao = DAO(path=resources_dir)
    projects = sorted(
        dao.get_all(),
        key=lambda item: (
            -(item.stars or 0),
            item.name,
        ),
    )

    # Label descriptions
    label_descriptions = {
        item["name"]: item["description"]
        for item in json.loads(Path(resources_dir, "labels.json").read_text())
    }

    # Website strings
    web_data = toml.loads((resources_dir / "website.toml").read_text())

    # Jinja templates
    environment = Environment(loader=FileSystemLoader("ecosystem/html_templates/"))
    templates = {
        "website": environment.get_template("webpage.html.jinja"),
        "card": environment.get_template("card.html.jinja"),
        "tag": environment.get_template("tag.html.jinja"),
        "link": environment.get_template("link.html.jinja"),
    }
    return projects, web_data, label_descriptions, templates

def _build_html(projects, web_data, label_descriptions, templates) -> str:
    """
    Take all data needed to build the website and produce a HTML string.
    """
    sections = {group["id"]: group for group in web_data["groups"]}
    for section in sections.values():
        section.setdefault("html", "")

    max_chars_description_visible = 400
    min_chars_description_hidden = 100
    count_read_more = 1
    for repo in projects:
        # Card tags
        tags = ""
        for index, label in enumerate(repo.labels):
            tags += templates["tag"].render(
                color="purple",
                text=label,
                tooltip=label_descriptions[label],
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
        header=web_data["header"],
        sections=sections.values(),
    )
