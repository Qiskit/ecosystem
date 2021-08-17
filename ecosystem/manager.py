"""Manager class for controlling all CLI functions."""
import os

from jinja2 import Environment, PackageLoader, select_autoescape

from .controller import Controller
from .entities import Tier, TestType
from .shell import basic_tests


class Manager:
    """Manager class.
    Entrypoint for all CLI commands.
    """

    def __init__(self):
        """Manager class."""
        current_dir = os.path.abspath(os.getcwd())
        self.resources_dir = "{}/ecosystem/resources".format(current_dir)

        self.env = Environment(
            loader=PackageLoader("ecosystem"),
            autoescape=select_autoescape()
        )
        self.readme_template = self.env.get_template("readme.md")
        self.controller = Controller(path=self.resources_dir)

    def generate_readme(self) -> str:
        """Generates entire readme for ecosystem repository.

        Returns:
            str: generated readme
        """
        main_repos = self.controller.get_all_main()
        return self.readme_template.render(main_repos=main_repos)

    def basic_test(self, repo_url: str,
                   tier: str = Tier.MAIN,
                   tox_python: str = "py39"):
        """Perform general checks for repository.

        Args:
            tox_python: version of python to run tox
            tier: repository tier
            repo_url: repository url
        """
        try:
            basic_tests_result = basic_tests(repo_url,
                                             resources_dir=self.resources_dir,
                                             tox_python=tox_python)
            # if all steps of test are successful
            if all(c.code == 0 for c in basic_tests_result.values()):
                # update repo entry and assign successful tests
                self.controller.add_repo_test_passed(repo_url=repo_url,
                                                     test_passed=TestType.STANDARD,
                                                     tier=tier)
            else:
                self.controller.remove_repo_test_passed(repo_url=repo_url,
                                                        test_remove=TestType.STANDARD,
                                                        tier=tier)
        except Exception as exception: # pylint: disable=broad-except)
            print(f"Exception {exception}")
            # remove from passed tests if anything went wrong
            self.controller.remove_repo_test_passed(repo_url=repo_url,
                                                    test_remove=TestType.STANDARD,
                                                    tier=tier)

    def __repr__(self):
        return "Manager(CLI entrypoint)"
