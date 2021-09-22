"""Manager class for controlling all CLI functions."""
import os
from typing import Optional, List

from jinja2 import Environment, PackageLoader, select_autoescape

from ecosystem.daos import JsonDAO
from ecosystem.models import TestResult, Tier, TestType
from ecosystem.models.test_results import StyleResult
from ecosystem.runners import PythonTestsRunner
from ecosystem.runners.python_styles_runner import PythonStyleRunner
from ecosystem.utils import logger


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
        self.pylintrc_template = self.env.get_template(".pylintrc")
        self.controller = JsonDAO(path=self.resources_dir)
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
                           style_type: str):
        """Runs tests using python runner.

        Args:
            repo_url: repository url
            tier: tier of project
            style_type: [dev, stable]
        """
        runner = PythonStyleRunner(repo_url,
                                   working_directory=self.resources_dir)
        _, results = runner.run()
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
