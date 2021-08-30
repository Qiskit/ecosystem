"""Manager class for controlling all CLI functions."""
import os
from typing import Optional

from jinja2 import Environment, PackageLoader, select_autoescape

from .controller import Controller
from .controllers.runner import PythonRunner
from .entities import Tier, TestType, TestResult
from .utils import logger


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

    def stable_tests(self, repo_url: str,
                     tier: str = Tier.MAIN,
                     python_version: str = "py39",):
        """Runs tests against stable version of qiskit."""
        runner = PythonRunner(repo_url,
                              working_directory=self.resources_dir,
                              ecosystem_deps=["qiskit"],
                              python_version=python_version)
        terra_version, results = runner.run()

        test_result = TestResult(passed=all(r.ok for r in results),
                                 terra_version=terra_version,
                                 test_type=TestType.STABLE_COMPATIBLE)
        # save test res to db
        result = self.controller.add_repo_test_result(repo_url=repo_url,
                                                      tier=tier,
                                                      test_result=test_result)
        # print report
        if result is None:
            self.logger.warning("Test result was not saved."
                                "There is not repo for url %s", repo_url)
        self.logger.info("Test results: %s", test_result)

        return terra_version
