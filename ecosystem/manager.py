"""Manager class for controlling all CLI functions."""
import os

from jinja2 import Environment, PackageLoader, select_autoescape

from ecosystem import Controller


class Manager:
    """Manager class.
    Entrypoint for all CLI commands.
    """

    def __init__(self):
        """Manager class."""
        current_dir = os.path.abspath(os.getcwd())
        resources_dir = "{}/ecosystem/resources".format(current_dir)

        self.env = Environment(
            loader=PackageLoader("ecosystem"),
            autoescape=select_autoescape()
        )
        self.readme_template = self.env.get_template("readme.md")
        self.controller = Controller(path=resources_dir)

    def generate_readme(self) -> str:
        """Generates entire readme for ecosystem repository.

        Returns:
            str: generated readme
        """
        main_repos = self.controller.get_all_main()
        return self.readme_template.render(main_repos=main_repos)

    def __repr__(self):
        return "Manager(CLI entrypoint)"
