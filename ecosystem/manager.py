"""Manager class for controlling all CLI functions."""
import os
from typing import Optional

from jinja2 import Environment, PackageLoader, select_autoescape

from .controller import Controller
from .entities import Tier, TestType
from .shell import basic_tests, stable_tests


class Manager:
    """Manager class.
    Entrypoint for all CLI commands.
    """

    def __init__(self):
        """Manager class."""
        self.current_dir = os.path.abspath(os.getcwd())
        self.resources_dir = "{}/ecosystem/resources".format(self.current_dir)

        self.env = Environment(
            loader=PackageLoader("ecosystem"),
            autoescape=select_autoescape()
        )
        self.readme_template = self.env.get_template("readme.md")
        self.stable_rox_template = self.env.get_template("stable_tox.ini")
        self.controller = Controller(path=self.resources_dir)

    def generate_readme(self, path: Optional[str] = None):
        """Generates entire readme for ecosystem repository.

        Returns:
            str: generated readme
        """
        path = path if path is not None else self.current_dir
        main_repos = self.controller.get_all_main()
        readme_content = self.readme_template.render(main_repos=main_repos)
        with open(f"{path}/README.md", "w") as file:
            file.write(readme_content)

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
            if all(c.ok for c in basic_tests_result.values()):
                # update repo entry and assign successful tests
                self.controller.add_repo_test_passed(repo_url=repo_url,
                                                     test_passed=TestType.STANDARD,
                                                     tier=tier)
            else:
                self.controller.remove_repo_test_passed(repo_url=repo_url,
                                                        test_remove=TestType.STANDARD,
                                                        tier=tier)
        except Exception as exception:  # pylint: disable=broad-except)
            print(f"Exception {exception}")
            # remove from passed tests if anything went wrong
            self.controller.remove_repo_test_passed(repo_url=repo_url,
                                                    test_remove=TestType.STANDARD,
                                                    tier=tier)

    def stable_test(self,
                    repo_url: str,
                    tier: str = Tier.MAIN,
                    tox_python: str = "py39"):
        """Runs tests against stable version of Qiskit."""
        try:
            stable_tests_results = stable_tests(repo_url,
                                                resources_dir=self.resources_dir,
                                                tox_python=tox_python,
                                                template=self.stable_rox_template)
            # if all steps of test are successful
            if all(c.ok for c in stable_tests_results.values()):
                # update repo entry and assign successful tests
                self.controller.add_repo_test_passed(repo_url=repo_url,
                                                     test_passed=TestType.STABLE_COMPATIBLE,
                                                     tier=tier)
            else:
                self.controller.remove_repo_test_passed(repo_url=repo_url,
                                                        test_remove=TestType.STABLE_COMPATIBLE,
                                                        tier=tier)
        except Exception as exception:  # pylint: disable=broad-except)
            print(f"Exception {exception}")
            # remove from passed tests if anything went wrong
            self.controller.remove_repo_test_passed(repo_url=repo_url,
                                                    test_remove=TestType.STABLE_COMPATIBLE,
                                                    tier=tier)

    def __repr__(self):
        return "Manager(CLI entrypoint)"
