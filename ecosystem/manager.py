"""Manager class for controlling all CLI functions."""
import os
from typing import Optional, List, Tuple

from jinja2 import Environment, PackageLoader, select_autoescape

from ecosystem.daos import JsonDAO
from ecosystem.models import TestResult, Tier, TestType
from ecosystem.models.repository import Repository
from ecosystem.models.test_results import StyleResult, CoverageResult
from ecosystem.runners import PythonTestsRunner
from ecosystem.runners.python_styles_runner import PythonStyleRunner
from ecosystem.runners.python_coverages_runner import PythonCoverageRunner
from ecosystem.utils import logger, parse_submission_issue
from ecosystem.utils.utils import set_actions_output


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
            loader=PackageLoader("ecosystem"), autoescape=select_autoescape()
        )
        self.readme_template = self.env.get_template("readme.md")
        self.pylintrc_template = self.env.get_template(".pylintrc")
        self.coveragerc_template = self.env.get_template(".coveragerc")
        self.controller = JsonDAO(path=self.resources_dir)
        self.logger = logger

    @staticmethod
    def parser_issue(body: str) -> None:
        """Command for calling body issue parsing function.

        Args:
            body: body of the created issue
        Returns:
            logs output
            We want to give the result of the parsing issue to the GitHub action
        """

        parsed_result = parse_submission_issue(body)

        to_print = [
            ("SUBMISSION_NAME", parsed_result.name),
            ("SUBMISSION_REPO", parsed_result.url),
            ("SUBMISSION_DESCRIPTION", parsed_result.description),
            ("SUBMISSION_LICENCE", parsed_result.licence),
            ("SUBMISSION_CONTACT", parsed_result.contact_info),
            ("SUBMISSION_ALTERNATIVES", parsed_result.alternatives),
            ("SUBMISSION_AFFILIATIONS", parsed_result.affiliations),
            ("SUBMISSION_LABELS", parsed_result.labels),
        ]

        set_actions_output(to_print)

    def add_repo_2db(
        self,
        repo_author: str,
        repo_link: str,
        repo_description: str,
        repo_licence: str,
        repo_contact: str,
        repo_alt: str,
        repo_affiliations: str,
        repo_labels: Tuple[str],
    ) -> None:
        """Adds repo to list of entries.
        Args:
            repo_author: repo author
            repo_link: repo url
            repo_description: repo description
            repo_contact: repo email
            repo_alt: repo alternatives
            repo_licence: repo licence
            repo_affiliations: repo university, company, ...
            repo_labels: comma separated labels
        Returns:
            JsonDAO: Integer
        """

        new_repo = Repository(
            repo_author,
            repo_link,
            repo_description,
            repo_licence,
            repo_contact,
            repo_alt,
            repo_affiliations,
            repo_labels,
        )
        self.controller.insert(new_repo)

    def generate_readme(self, path: Optional[str] = None):
        """Generates entire readme for ecosystem repository.

        Returns:
            str: generated readme
        """
        path = path if path is not None else self.current_dir
        main_repos = self.controller.get_repos_by_tier(Tier.MAIN)
        readme_content = self.readme_template.render(main_repos=main_repos)
        with open(f"{path}/README.md", "w") as file:
            file.write(readme_content)

    def _run_python_tests(
        self,
        repo_url: str,
        tier: str,
        python_version: str,
        test_type: str,
        ecosystem_deps: Optional[List[str]] = None,
    ):
        """Runs tests using python runner.

        Args:
            repo_url: repository url
            tier: tier of project
            python_version: ex: py36, py37 etc
            test_type: [dev, stable]
            ecosystem_deps: extra dependencies to install for tests
        Return:
            output: log PASS
            We want to give the result of the test to the GitHub action
        """
        ecosystem_deps = ecosystem_deps or []
        runner = PythonTestsRunner(
            repo_url,
            working_directory=self.resources_dir,
            ecosystem_deps=ecosystem_deps,
            python_version=python_version,
        )
        terra_version, results = runner.run()
        if len(results) > 0:
            test_result = TestResult(
                passed=all(r.ok for r in results),
                terra_version=terra_version,
                test_type=test_type,
            )
            # save test res to db
            result = self.controller.add_repo_test_result(
                repo_url=repo_url, tier=tier, test_result=test_result
            )
            # print report
            if result is None:
                self.logger.warning(
                    "Test result was not saved." "There is not repo for url %s",
                    repo_url,
                )
            self.logger.info("Test results for %s: %s", repo_url, test_result)
            set_actions_output([("PASS", test_result.passed + " - " + test_result.terra_version)])
        else:
            self.logger.warning("Runner returned 0 results.")
            set_actions_output([("PASS", "False")])

        return terra_version

    def python_styles_check(self, repo_url: str, tier: str, style_type: str):
        """Runs tests using python runner.

        Args:
            repo_url: repository url
            tier: tier of project
            style_type: [dev, stable]
        Return:
            output: log PASS
            We want to give the result of the test to the GitHub action
        """
        runner = PythonStyleRunner(repo_url, working_directory=self.resources_dir)
        _, results = runner.run()
        if len(results) > 0:
            style_result = StyleResult(
                passed=all(r.ok for r in results), style_type=style_type
            )
            # save test res to db
            result = self.controller.add_repo_style_result(
                repo_url=repo_url, tier=tier, style_result=style_result
            )
            # print report
            if result is None:
                self.logger.warning(
                    "Test result was not saved." "There is not repo for url %s",
                    repo_url,
                )
            self.logger.info("Test results for %s: %s", repo_url, style_result)
            set_actions_output([("PASS", style_result.passed)])
        else:
            self.logger.warning("Runner returned 0 results.")
            set_actions_output([("PASS", "False")])

    def python_coverage(self, repo_url: str, tier: str, coverage_type: str):
        """Runs tests using python runner.

        Args:
            repo_url: repository url
            tier: tier of project
            coverage_type: [dev, stable]
        Return:
            output: log PASS
            We want to give the result of the test to the GitHub action
        """
        runner = PythonCoverageRunner(repo_url, working_directory=self.resources_dir)
        _, results = runner.run()
        if len(results) > 0:
            coverage_result = CoverageResult(
                passed=all(r.ok for r in results), coverage_type=coverage_type
            )
            # save test res to db
            result = self.controller.add_repo_coverage_result(
                repo_url=repo_url, tier=tier, coverage_result=coverage_result
            )
            # print report
            if result is None:
                self.logger.warning(
                    "Test result was not saved." "There is not repo for url %s",
                    repo_url,
                )
            self.logger.info("Test results for %s: %s", repo_url, coverage_result)
            set_actions_output([("PASS", coverage_result.passed)])
        else:
            self.logger.warning("Runner returned 0 results.")
            set_actions_output([("PASS", "False")])

    def python_dev_tests(
        self, repo_url: str, tier: str = Tier.MAIN, python_version: str = "py39"
    ):
        """Runs tests against dev version of qiskit."""
        return self._run_python_tests(
            repo_url=repo_url,
            tier=tier,
            python_version=python_version,
            test_type=TestType.DEV_COMPATIBLE,
            ecosystem_deps=["git+https://github.com/Qiskit/qiskit-terra.git@main"],
        )

    def python_stable_tests(
        self, repo_url: str, tier: str = Tier.MAIN, python_version: str = "py39"
    ):
        """Runs tests against stable version of qiskit."""
        return self._run_python_tests(
            repo_url=repo_url,
            tier=tier,
            python_version=python_version,
            test_type=TestType.STABLE_COMPATIBLE,
            ecosystem_deps=["qiskit"],
        )
