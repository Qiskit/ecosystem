"""Manager class for controlling all CLI functions."""
import os
from typing import Optional, List, Tuple

import requests
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

    def __init__(self, root_path: Optional[str] = None):
        """Manager class."""
        self.current_dir = root_path or os.path.abspath(os.getcwd())
        self.resources_dir = "{}/ecosystem/resources".format(self.current_dir)

        self.env = Environment(
            loader=PackageLoader("ecosystem"), autoescape=select_autoescape()
        )
        self.readme_template = self.env.get_template("readme.md")
        self.pylintrc_template = self.env.get_template(".pylintrc")
        self.coveragerc_template = self.env.get_template(".coveragerc")
        self.dao = JsonDAO(path=self.resources_dir)
        self.logger = logger

    def dispatch_check_workflow(
        self,
        repo_url: str,
        issue_id: str,
        branch_name: str,
        tier: str,
        token: str,
        owner: str = "qiskit-community",
        repo: str = "ecosystem",
    ) -> bool:
        """Dispatch event to trigger check workflow."""
        url = "https://api.github.com/repos/{owner}/{repo}/dispatches".format(
            owner=owner, repo=repo
        )
        repo_split = repo_url.split("/")
        repo_name = repo_split[-1]

        response = requests.post(
            url,
            json={
                "event_type": "check_project",
                "client_payload": {
                    "repo_url": repo_url,
                    "repo_name": repo_name,
                    "issue_id": issue_id,
                    "branch_name": branch_name,
                    "tier": tier,
                },
            },
            headers={
                "Authorization": "token {}".format(token),
                "Accept": "application/vnd.github.v3+json",
            },
        )
        if response.ok:
            self.logger.info("Success response on dispatch event. %s", response.text)
        else:
            self.logger.warning(
                "Something wend wrong with dispatch event: %s", response.text
            )
        return response.ok

    def dispatch_badge_workflow(
        self,
        repo_url: str,
        tests: str,
        issue_id: str,
        branch_name: str,
        token: str,
        owner: str = "qiskit-community",
        repo: str = "ecosystem",
    ) -> bool:
        """Dispatch event to trigger check workflow."""
        url = "https://api.github.com/repos/{owner}/{repo}/dispatches".format(
            owner=owner, repo=repo
        )
        repo_split = repo_url.split("/")
        repo_name = repo_split[-1]

        response = requests.post(
            url,
            json={
                "event_type": "badge_project",
                "client_payload": {
                    "repo_name": repo_name,
                    "tests": tests,
                    "issue_id": issue_id,
                    "branch_name": branch_name,
                },
            },
            headers={
                "Authorization": "token {}".format(token),
                "Accept": "application/vnd.github.v3+json",
            },
        )
        if response.ok:
            self.logger.info("Success response on dispatch event. %s", response.text)
        else:
            self.logger.warning(
                "Something wend wrong with dispatch event: %s", response.text
            )
        return response.ok

    def get_projects_by_tier(self, tier: str) -> None:
        """Return projects by tier.

        Args:
            tier: tier of ecosystem
        """
        tests = []
        repositories = ",".join([repo.url for repo in self.dao.get_repos_by_tier(tier)])
        tests_list = [repo.tests_results for repo in self.dao.get_repos_by_tier(tier)]

        for i in tests_list:
            test_result = [str(repo.passed) for repo in i]
            if "False" not in test_result:
                tests.append("True")
            else:
                tests.append("False")

        set_actions_output([("repositories", repositories)])
        set_actions_output([("tests", ",".join(tests))])

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
        repo_name: str,
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
            repo_name: repo name
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
            repo_name,
            repo_link,
            repo_description,
            repo_licence,
            repo_contact,
            repo_alt,
            repo_affiliations,
            list(repo_labels),
        )
        self.dao.insert(new_repo)

    def generate_readme(self, path: Optional[str] = None):
        """Generates entire readme for ecosystem repository.

        Returns:
            str: generated readme
        """
        path = path if path is not None else self.current_dir
        main_repos = self.dao.get_repos_by_tier(Tier.MAIN)
        community_repos = self.dao.get_repos_by_tier(Tier.COMMUNITY)
        readme_content = self.readme_template.render(
            main_repos=main_repos, community_repos=community_repos
        )
        with open(f"{path}/README.md", "w") as file:
            file.write(readme_content)

    def _run_python_tests(
        self,
        repo_url: str,
        tier: str,
        python_version: str,
        test_type: str,
        ecosystem_deps: Optional[List[str]] = None,
        ecosystem_additional_commands: Optional[List[str]] = None,
    ):
        """Runs tests using python runner.

        Args:
            repo_url: repository url
            tier: tier of project
            python_version: ex: py36, py37 etc
            test_type: [dev, stable]
            ecosystem_deps: extra dependencies to install for tests
            ecosystem_additional_commands: extra commands to run before tests
        Return:
            output: log PASS
            We want to give the result of the test to the GitHub action
        """
        ecosystem_deps = ecosystem_deps or []
        ecosystem_additional_commands = ecosystem_additional_commands or []
        runner = PythonTestsRunner(
            repo_url,
            working_directory=self.resources_dir,
            ecosystem_deps=ecosystem_deps,
            ecosystem_additional_commands=ecosystem_additional_commands,
            python_version=python_version,
        )
        terra_version, results = runner.run()
        if len(results) > 0:
            # if default tests are passed
            # we do not detect deprecation warnings for qiskit
            if test_type == TestType.STANDARD:
                passed = all(r.ok for r in results)
            else:
                passed = all(
                    r.ok and not r.has_qiskit_deprecation_logs for r in results
                )

            test_result = TestResult(
                passed=passed,
                terra_version=terra_version,
                test_type=test_type,
            )
            # save test res to db
            result = self.dao.add_repo_test_result(
                repo_url=repo_url, tier=tier, test_result=test_result
            )
            # print report
            if result is None:
                self.logger.warning(
                    "Test result was not saved." "There is not repo for url %s",
                    repo_url,
                )
            self.logger.info("Test results for %s: %s", repo_url, test_result)
            set_actions_output(
                [
                    (
                        "PASS",
                        f"{test_result.passed} - Terra version : {test_result.terra_version}",
                    )
                ]
            )
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
            result = self.dao.add_repo_style_result(
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
            result = self.dao.add_repo_coverage_result(
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
        # hack to fix tox's inability to install proper version of
        # qiskit through github via deps configuration
        additional_commands = [
            "pip uninstall -y qiskit-terra",
            "pip install git+https://github.com/Qiskit/qiskit-terra.git@main",
        ]
        return self._run_python_tests(
            repo_url=repo_url,
            tier=tier,
            python_version=python_version,
            test_type=TestType.DEV_COMPATIBLE,
            ecosystem_deps=[],
            ecosystem_additional_commands=additional_commands,
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

    def python_standard_tests(
        self, repo_url: str, tier: str = Tier.MAIN, python_version: str = "py39"
    ):
        """Runs tests with provided confiuration."""
        return self._run_python_tests(
            repo_url=repo_url,
            tier=tier,
            python_version=python_version,
            test_type=TestType.STANDARD,
        )
