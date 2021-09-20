"""Manager class for controlling all CLI functions."""
import os
import re
from typing import Optional, List

from jinja2 import Environment, PackageLoader, select_autoescape

from .controller import Controller
from .controllers.runner import PythonTestsRunner, PythonStyleRunner
from .entities import Tier, TestType, TestResult, StyleResult, Repository
from .utils import logger


def parse_submission_issue(body_of_issue: str) -> Repository:
    """Parse issue body."""

    parse = re.findall(r'^([\s\S]*?)(?:\n{2,}|\Z)', body_of_issue, re.M)

    repo_name = parse[1].split("/")

    name = repo_name[-1]
    url = parse[1]
    description = parse[3]
    contact_info = parse[5]
    alternatives = parse[7]
    licence = parse[9]
    affiliations = parse[11]

    labels = re.findall(r"([\w\]+)([\w\-\_]+)", parse[13])

    repo = Repository(name, url, description, licence,
                      contact_info, alternatives, affiliations, labels)
    return repo


class Manager:
    """Manager class.
    Entrypoint for all CLI commands.

    Each public method of this class is CLI command
    and arguments for method are options/flags for this command.

    Ex: `python manager.py generate_readme --path=<SOME_DIRECTORY>`
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
        self.logger = logger

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

    def _run_python_tests(self,
                          repo_url: str,
                          tier: str,
                          python_version: str,
                          test_type: str,
                          ecosystem_deps: Optional[List[str]] = None):
        """Runs tests using python runner.

        Args:
            repo_url: repository url
            tier: tier of project
            python_version: ex: py36, py37 etc
            test_type: [dev, stable]
            ecosystem_deps: extra dependencies to install for tests
        """
        ecosystem_deps = ecosystem_deps or []
        runner = PythonTestsRunner(repo_url,
                                   working_directory=self.resources_dir,
                                   ecosystem_deps=ecosystem_deps,
                                   python_version=python_version)
        terra_version, results = runner.run()
        if len(results) > 0:
            test_result = TestResult(passed=all(r.ok for r in results),
                                     terra_version=terra_version,
                                     test_type=test_type)
            # save test res to db
            result = self.controller.add_repo_test_result(repo_url=repo_url,
                                                          tier=tier,
                                                          test_result=test_result)
            # print report
            if result is None:
                self.logger.warning("Test result was not saved."
                                    "There is not repo for url %s", repo_url)
            self.logger.info("Test results for %s: %s", repo_url, test_result)
        else:
            self.logger.warning("Runner returned 0 results.")

        return terra_version

    def _run_python_styles(self,
                           repo_url: str,
                           tier: str,
                           style_type: str,
                           ecosystem_deps: Optional[List[str]] = None):
        """Runs tests using python runner.

        Args:
            repo_url: repository url
            tier: tier of project
            style_type: [dev, stable]
            ecosystem_deps: extra dependencies to install for tests
        """
        ecosystem_deps = ecosystem_deps or []
        runner = PythonStyleRunner(repo_url,
                                   working_directory=self.resources_dir,
                                   ecosystem_deps=ecosystem_deps)
        results = runner.run()
        if len(results) > 0:
            style_result = StyleResult(passed=all(r.ok for r in results),
                                       style_type=style_type)
            # save test res to db
            result = self.controller.add_repo_style_result(repo_url=repo_url,
                                                           tier=tier,
                                                           style_result=style_result)
            # print report
            if result is None:
                self.logger.warning("Test result was not saved."
                                    "There is not repo for url %s", repo_url)
            self.logger.info("Test results for %s: %s", repo_url, style_result)
        else:
            self.logger.warning("Runner returned 0 results.")

    def python_dev_tests(self,
                         repo_url: str,
                         tier: str = Tier.MAIN,
                         python_version: str = "py39"):
        """Runs tests against dev version of qiskit."""
        return self._run_python_tests(
            repo_url=repo_url,
            tier=tier,
            python_version=python_version,
            test_type=TestType.DEV_COMPATIBLE,
            ecosystem_deps=["git+https://github.com/Qiskit/qiskit-terra.git@main"])

    def python_stable_tests(self,
                            repo_url: str,
                            tier: str = Tier.MAIN,
                            python_version: str = "py39"):
        """Runs tests against stable version of qiskit."""
        return self._run_python_tests(
            repo_url=repo_url,
            tier=tier,
            python_version=python_version,
            test_type=TestType.STABLE_COMPATIBLE,
            ecosystem_deps=["qiskit"])
