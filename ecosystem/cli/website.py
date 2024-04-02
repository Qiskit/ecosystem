"""CliWebsite class for controlling all CLI functions."""
from __future__ import annotations


from pathlib import Path
from typing import Any
import json
import re
import toml

from jinja2 import Environment, PackageLoader, Template

from ecosystem.daos import DAO
from ecosystem.models.repository import Repository


def build_website(resources: str, output: str) -> None:
    """
    Generates the ecosystem web page from data in `resources` dir, writing to `output` dir.
    """
    projects, web_data, label_descriptions, templates, custom_css = _load_from_file(
        Path(resources)
    )
    html = _build_html(projects, web_data, label_descriptions, templates)
    Path(output).write_text(html)

    css = templates["css"].render(
        custom_css=custom_css, standalone=web_data.get("standalone", True)
    )
    (Path(output).parent / "style.css").write_text(css)


def _load_from_file(
    resources_dir: Path,
) -> tuple[
    list[Repository], dict[str, Any], dict[str, str], dict[str, Template], str | None
]:
    """
    Loads website data from file.
    Returns:
        * Projects: List of Repository objects from `members` folder.
        * Web data: Strings (title / descriptions etc.) from `website.toml`.
        * Label descriptions: from `labels.json`.
        * Jinja templates: from `html_templates` folder.
        * Any custom css to be appended to the css file.
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
    label_descriptions = json.loads((resources_dir / "labels.json").read_text())

    # Website strings
    web_data = toml.loads((resources_dir / "website.toml").read_text())

    # Custom css
    custom_css = None
    if web_data.get("custom-css", False):
        custom_css = (resources_dir / web_data["custom-css"]).read_text()

    # Jinja templates
    environment = Environment(loader=PackageLoader("ecosystem", "html_templates/"))
    templates = {
        "website": environment.get_template("webpage.html.jinja"),
        "card": environment.get_template("card.html.jinja"),
        "tag": environment.get_template("tag.html.jinja"),
        "link": environment.get_template("link.html.jinja"),
        "css": environment.get_template("style.css.jinja"),
    }
    return projects, web_data, label_descriptions, templates, custom_css


def _build_html(projects, web_data, label_descriptions, templates) -> str:
    """
    Take all data needed to build the website and produce a HTML string.
    """
    # pylint: disable=too-many-locals
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

    html = templates["website"].render(
        is_standalone=web_data.get("standalone", True),
        header=web_data["header"],
        sections=sections.values(),
    )
    return re.sub(r"^\s+", "", html, flags=re.MULTILINE)
