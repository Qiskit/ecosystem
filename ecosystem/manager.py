"""Manager class for controlling all CLI functions."""
import os
from typing import Optional, List

from jinja2 import Environment, PackageLoader, select_autoescape

from .controller import Controller
from .entities import Tier, TestType
from .commands import run_tests
from .logging import logger


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
        self.tox_template = self.env.get_template("tox.ini")
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

    def _run(self,
             repo_url: str,
             tier: str,
             test_type: str,
             tox_python: str,
             dependencies: Optional[List[str]] = None):
        """Run tests on repository.

        Args:
            repo_url: repository url
            tier: tier of membership
            tox_python: tox env to run tests on
            dependencies: list of extra dependencies to install
        """
        try:
            if dependencies is not None:
                dev_tests_results = run_tests(
                    repo_url,
                    resources_dir=self.resources_dir,
                    tox_python=tox_python,
                    template_and_deps=(self.tox_template, dependencies))
            else:
                dev_tests_results = run_tests(
                    repo_url,
                    resources_dir=self.resources_dir,
                    tox_python=tox_python)
            # if all steps of test are successful
            if all(c.ok for c in dev_tests_results.values()):
                # update repo entry and assign successful tests
                self.controller.add_repo_test_passed(repo_url=repo_url,
                                                     test_passed=test_type,
                                                     tier=tier)
            else:
                logger.warning("Some commands failed. Check logs.")
                self.controller.remove_repo_test_passed(repo_url=repo_url,
                                                        test_remove=test_type,
                                                        tier=tier)
        except Exception as exception:  # pylint: disable=broad-except)
            logger.error("Exception: %s", exception)
            # remove from passed tests if anything went wrong
            self.controller.remove_repo_test_passed(repo_url=repo_url,
                                                    test_remove=test_type,
                                                    tier=tier)

    def standard_tests(self, repo_url: str,
                       tier: str = Tier.MAIN,
                       tox_python: str = "py39"):
        """Perform general checks for repository."""
        return self._run(repo_url=repo_url,
                         tier=tier,
                         test_type=TestType.STANDARD,
                         tox_python=tox_python)

    def stable_compatibility_tests(self,
                                   repo_url: str,
                                   tier: str = Tier.MAIN,
                                   tox_python: str = "py39"):
        """Runs tests against stable version of Qiskit."""
        return self._run(repo_url=repo_url,
                         tier=tier,
                         test_type=TestType.STABLE_COMPATIBLE,
                         tox_python=tox_python,
                         dependencies=["qiskit"])

    def dev_compatibility_tests(self,
                                repo_url: str,
                                tier: str = Tier.MAIN,
                                tox_python: str = "py39"):
        """Runs tests against dev version of Qiskit (main branch)."""
        return self._run(repo_url=repo_url,
                         tier=tier,
                         test_type=TestType.DEV_COMPATIBLE,
                         tox_python=tox_python,
                         dependencies=["git+https://github.com/Qiskit/qiskit-terra.git@main"])

    def __repr__(self):
        return "Manager(CLI entrypoint)"
