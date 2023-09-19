"""Manager class for controlling all CLI functions."""
import glob
import json
import os
import shutil
import uuid
from typing import Optional, List, Tuple, Union

import requests
from jinja2 import Environment, PackageLoader, select_autoescape

from ecosystem.daos import DAO
from ecosystem.models import TestResult, Tier, TestType
from ecosystem.models.repository import Repository
from ecosystem.models.test_results import StyleResult, CoverageResult, Package
from ecosystem.runners import PythonTestsRunner
from ecosystem.runners.main_repos_report_runner import RepositoryActionStatusRunner
from ecosystem.runners.python_styles_runner import PythonStyleRunner
from ecosystem.runners.python_coverages_runner import PythonCoverageRunner
from ecosystem.utils import logger, parse_submission_issue
from ecosystem.utils.custom_requests import (
    get_dev_qiskit_version,
    get_stable_qiskit_version,
)
from ecosystem.utils.utils import set_actions_output


class Manager:
    """Manager class.
    Entrypoint for all CLI commands.

    Each public method of this class is CLI command
    and arguments for method are options/flags for this command.

    Ex: `python manager.py parser_issue --body="<SOME_MARKDOWN>"`
    """

    def __init__(self, root_path: Optional[str] = None):
        """Manager class."""
        self.current_dir = root_path or os.path.abspath(os.getcwd())
        self.resources_dir = "{}/ecosystem/resources".format(self.current_dir)

        self.env = Environment(
            loader=PackageLoader("ecosystem"), autoescape=select_autoescape()
        )
        self.pylintrc_template = self.env.get_template(".pylintrc")
        self.coveragerc_template = self.env.get_template(".coveragerc")
        self.dao = DAO(path=self.resources_dir)
        self.logger = logger

    def recompile(self):
        """Recompile `members.json` from human-readable files."""
        self.dao.compile_json()

    def dispatch_check_workflow(
        self,
        repo_url: str,
        branch_name: str,
        tier: str,
        token: str,
        owner: str = "qiskit-community",
        repo: str = "ecosystem",
    ) -> bool:
        """Dispatch event to trigger check workflow.

        Args:
            repo_url: url of the repo
            branch_name: name of the branch
            tier: tier of the project
            token: token base on the date
            owner: "qiskit-community" parameters
            repo: "ecosystem"

        Return: true
        """
        url = "https://api.github.com/repos/{owner}/{repo}/dispatches".format(
            owner=owner, repo=repo
        )
        repo_split = repo_url.split("/")
        repo_name = repo_split[-1]

        # run each type of tests in same workflow
        response = requests.post(
            url,
            json={
                "event_type": "check_project",
                "client_payload": {
                    "repo_url": repo_url,
                    "repo_name": repo_name,
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
        return True

    def expose_all_project_to_actions(self):
        """Exposes all project for github actions."""
        repositories = []
        tiers = []
        for tier in Tier.non_main_tiers():
            for repo in self.dao.get_repos_by_tier(tier):
                if not repo.skip_tests:
                    repositories.append(repo.url)
                    tiers.append(repo.tier)
        set_actions_output(
            [("repositories", ",".join(repositories)), ("tiers", ",".join(tiers))]
        )

    def update_badges(self):
        """Updates badges for projects."""
        badges_folder_path = "{}/badges".format(self.current_dir)

        for tier in Tier.all():
            for project in self.dao.get_repos_by_tier(tier):
                tests_passed = True
                for type_test in project.tests_results:
                    if type_test.test_type == "standard" and not type_test.passed:
                        tests_passed = False
                color = "blueviolet" if tests_passed else "gray"
                label = project.name
                message = tier
                url = (
                    f"https://img.shields.io/static/v1?"
                    f"label={label}&message={message}&color={color}"
                )

                shields_request = requests.get(url)
                with open(f"{badges_folder_path}/{project.name}.svg", "wb") as outfile:
                    outfile.write(shields_request.content)
                    self.logger.info("Badge for %s has been updated.", project.name)

    def update_stars(self):
        """Updates start for repositories."""
        for tier in Tier.all():
            for project in self.dao.get_repos_by_tier(tier):
                stars = None
                url = project.url[:-1] if project.url[-1] == "/" else project.url
                url_chunks = url.split("/")
                repo = url_chunks[-1]
                user = url_chunks[-2]

                response = requests.get(f"http://api.github.com/repos/{user}/{repo}")
                if not response.ok:
                    self.logger.warning("Bad response for project %s", project.url)
                    continue

                json_data = json.loads(response.text)
                stars = json_data.get("stargazers_count")
                self.dao.update(project.url, stars=stars)
                self.logger.info("Updating star count for %s: %d", project.url, stars)

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
            ("SUBMISSION_WEBSITE", parsed_result.website),
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
        repo_tier: Optional[str] = None,
        repo_website: Optional[str] = None,
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
            repo_tier: tier for repository
            repo_website: link to project website
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
            tier=repo_tier or Tier.COMMUNITY,
            website=repo_website,
        )
        self.dao.write(new_repo)

    def _save_temp_test_result(
        self,
        folder_name: str,
        repo_url: str,
        tier: str,
        test_result: Union[TestResult, StyleResult, CoverageResult],
    ) -> None:
        """Saves result to temp file.

        Args:
            folder_name: name of folder to store temp files
            repo_url: project repo url
            test_result: test result
        """
        folder_full_path = "{}/{}".format(self.resources_dir, folder_name)
        # make dir
        if not os.path.exists(folder_full_path):
            os.makedirs(folder_full_path)

        file_name = "{}/{}.json".format(folder_full_path, uuid.uuid4())

        with open(file_name, "w") as json_temp_file:
            json_temp_file.write(
                json.dumps(
                    {
                        "repo_url": repo_url,
                        "tier": tier,
                        "type": type(test_result).__name__,
                        "test_result": test_result.to_dict(),
                    }
                )
            )
    def add_test_result(self, json_file):
        with open(json_file) as f:
            test_json = json.load(f)
        repo_name = test_json.pop('repo_name')
        repo_url = f"https://github.com/{repo_name}"
        test_result = TestResult.from_dict(test_json)
        self.dao.add_repo_test_result(repo_url=repo_url, test_result=test_result)

    def list_repos_for_testing(self):
        """
        Returns JSON string of repos to test
        """
        repo_names = []
        for repo in self.dao.storage.read().values():
            if not repo.skip_tests:
                name = "/".join(repo.url.split("/")[3:5])
                repo_names.append(name)
        return json.dumps(repo_names)


    def process_temp_test_results_files(self, folder_name: str) -> None:
        """Process temp test results files and store data to DB.

        Args:
            folder_name: folder to store temp results

        Returns: number of saved entries
        """

        # read all files and push to DB
        folder_full_path = "{}/{}".format(self.resources_dir, folder_name)
        for path in glob.glob("{}/*.json".format(folder_full_path)):
            self.logger.info("Processing %s file...", path)
            with open(path, "r") as json_temp_file:
                json_temp_file_data = json.load(json_temp_file)
                repo_url = json_temp_file_data.get("repo_url")
                test_type = json_temp_file_data.get("type")
                test_result = json_temp_file_data.get("test_result")
                self.logger.info(
                    "Processing test results for project: " "%s %s",
                    repo_url,
                    test_result,
                )
                if test_type == "TestResult":
                    tres = TestResult.from_dict(test_result)
                    self.dao.add_repo_test_result(repo_url=repo_url, test_result=tres)
                elif test_type == "CoverageResult":
                    cres = CoverageResult.from_dict(test_result)
                    self.dao.add_repo_coverage_result(
                        repo_url=repo_url, coverage_result=cres
                    )
                elif test_type == "StyleResult":
                    sres = StyleResult.from_dict(test_result)
                    self.dao.add_repo_style_result(repo_url=repo_url, style_result=sres)
                else:
                    raise NotImplementedError(
                        "Test type {} is not supported".format(test_type)
                    )

        # remove temp files
        if os.path.exists(folder_full_path):
            self.logger.info("Removing temp folder %s", folder_full_path)
            shutil.rmtree(folder_full_path)

    def _run_python_tests(
        self,
        run_name: str,
        repo_url: str,
        tier: str,
        python_version: str,
        test_type: str,
        ecosystem_deps: Optional[List[str]] = None,
        ecosystem_additional_commands: Optional[List[str]] = None,
        logs_link: Optional[str] = None,
        package_commit_hash: Optional[str] = None,
        skip_deprecation_warnings: bool = True,
    ):
        """Runs tests using python runner.

        Args:
            run_name (str): name of the run
            repo_url: repository url
            tier: tier of project
            python_version: ex: py36, py37 etc
            test_type: [dev, stable]
            ecosystem_deps: extra dependencies to install for tests
            ecosystem_additional_commands: extra commands to run before tests
            logs_link: link to logs from gh actions
            package_commit_hash: commit hash for package
            skip_deprecation_warnings: deprecation warnings does not affect passing of tests

        Return:
            output: log PASS
            We want to give the result of the test to the GitHub action
        """
        ecosystem_deps = ecosystem_deps or []
        ecosystem_additional_commands = ecosystem_additional_commands or []
        repository = self.dao.get_by_url(repo_url)
        repo_configuration = (
            repository.configuration if repository is not None else None
        )

        runner = PythonTestsRunner(
            repo_url,
            working_directory=self.resources_dir,
            ecosystem_deps=ecosystem_deps,
            ecosystem_additional_commands=ecosystem_additional_commands,
            python_version=python_version,
            repo_config=repo_configuration,
        )
        qiskit_version, results = runner.run()
        if len(results) > 0:
            # if default tests are passed
            # we do not detect deprecation warnings for qiskit
            if test_type == TestType.STANDARD or skip_deprecation_warnings is True:
                passed = all(r.ok for r in results)
            else:
                passed = all(
                    r.ok and not r.has_qiskit_deprecation_logs for r in results
                )

            test_result = TestResult(
                passed=passed,
                package=Package.QISKIT,
                package_version=qiskit_version,
                test_type=test_type,
                logs_link=logs_link,
                package_commit_hash=package_commit_hash,
            )
            # saving results to temp files
            if run_name:
                self._save_temp_test_result(
                    folder_name=run_name,
                    repo_url=repo_url,
                    test_result=test_result,
                    tier=tier,
                )
            self.logger.info("Test results for %s: %s", repo_url, test_result)
            set_actions_output(
                [
                    (
                        "PASS",
                        f"{test_result.passed} - Qiskit version : {test_result.qiskit_version}",
                    )
                ]
            )
        else:
            self.logger.warning("Runner returned 0 results.")
            set_actions_output([("PASS", "False")])

        return qiskit_version

    def python_styles_check(
        self,
        run_name: str,
        repo_url: str,
        tier: str,  # pylint: disable=unused-argument
        style_type: str,
    ):
        """Runs tests using python runner.

        Args:
            run_name: name of the run
            repo_url: repository url
            tier: tier of project
            style_type: [dev, stable]

        Return:
            output: log PASS
            We want to give the result of the test to the GitHub action
        """
        repository = self.dao.get_by_url(repo_url)
        repo_configuration = (
            repository.configuration if repository is not None else None
        )
        runner = PythonStyleRunner(
            repo_url,
            working_directory=self.resources_dir,
            repo_config=repo_configuration,
        )
        _, results = runner.run()
        if len(results) > 0:
            style_result = StyleResult(
                passed=all(r.ok for r in results), style_type=style_type
            )
            # saving results to temp files
            if run_name:
                self._save_temp_test_result(
                    folder_name=run_name,
                    repo_url=repo_url,
                    test_result=style_result,
                    tier=tier,
                )
            self.logger.info("Test results for %s: %s", repo_url, style_result)
            set_actions_output([("PASS", style_result.passed)])
        else:
            self.logger.warning("Runner returned 0 results.")
            set_actions_output([("PASS", "False")])

    def python_coverage(
        self,
        run_name: str,
        repo_url: str,
        tier: str,  # pylint: disable=unused-argument
        coverage_type: str,
    ):
        """Runs tests using python runner.

        Args:
            run_name: name of the run
            repo_url: repository url
            tier: tier of project
            coverage_type: [dev, stable]

        Return:
            output: log PASS
            We want to give the result of the test to the GitHub action
        """
        repository = self.dao.get_by_url(repo_url)
        repo_configuration = (
            repository.configuration if repository is not None else None
        )
        runner = PythonCoverageRunner(
            repo_url,
            working_directory=self.resources_dir,
            repo_config=repo_configuration,
        )
        _, results = runner.run()
        if len(results) > 0:
            coverage_result = CoverageResult(
                passed=all(r.ok for r in results), coverage_type=coverage_type
            )
            # saving results to temp files
            if run_name:
                self._save_temp_test_result(
                    folder_name=run_name,
                    repo_url=repo_url,
                    test_result=coverage_result,
                    tier=tier,
                )
            self.logger.info("Test results for %s: %s", repo_url, coverage_result)
            set_actions_output([("PASS", coverage_result.passed)])
        else:
            self.logger.warning("Runner returned 0 results.")
            set_actions_output([("PASS", "False")])

    def python_dev_tests(
        self,
        run_name: str,
        repo_url: str,
        tier: str = Tier.MAIN,
        python_version: str = "py39",
        logs_link: Optional[str] = None,
    ):
        """Runs tests against dev version of qiskit.

        Args:
            logs_link: link to logs of github actions run
            run_name: name of the run
            repo_url: repository url
            tier: tier of project
            python_version: [py39, py37]

        Return:
            _run_python_tests def
        """
        package = "qiskit-terra"

        # get package commit hash
        package_commit_hash = None
        git_response = requests.get(
            f"https://api.github.com/repos/qiskit/{package}/commits/main"
        )
        if git_response.ok:
            commit_data = json.loads(git_response.text)
            package_commit_hash = commit_data.get("sha")
        else:
            self.logger.warning("Wan't able to parse package commit hash")

        # hack to fix tox's inability to install proper version of
        # qiskit through github via deps configuration
        additional_commands = [
            f"pip uninstall -y {package}",
            f"pip install git+https://github.com/Qiskit/{package}.git@main",
        ]
        return self._run_python_tests(
            run_name=run_name,
            repo_url=repo_url,
            tier=tier,
            python_version=python_version,
            test_type=TestType.DEV_COMPATIBLE,
            ecosystem_deps=[],
            ecosystem_additional_commands=additional_commands,
            logs_link=logs_link,
            package_commit_hash=package_commit_hash,
        )

    def python_stable_tests(
        self,
        run_name: str,
        repo_url: str,
        tier: str = Tier.MAIN,
        python_version: str = "py39",
        logs_link: Optional[str] = None,
    ):
        """Runs tests against stable version of qiskit.
        Args:
            run_name: name of the run
            repo_url: repository url
            tier: tier of project
            python_version: [py39, py37]
            logs_link: links to logs

        Return:
            _run_python_tests def
        """
        qiskit_latest_deps = ["qiskit"]
        additional_commands = [
            "pip install --upgrade --no-dependencies --force-reinstall qiskit",
        ]
        return self._run_python_tests(
            run_name=run_name,
            repo_url=repo_url,
            tier=tier,
            python_version=python_version,
            test_type=TestType.STABLE_COMPATIBLE,
            ecosystem_deps=qiskit_latest_deps,
            ecosystem_additional_commands=additional_commands,
            logs_link=logs_link,
        )

    def python_standard_tests(
        self,
        run_name: str,
        repo_url: str,
        tier: str = Tier.MAIN,
        python_version: str = "py39",
        logs_link: Optional[str] = None,
    ):
        """Runs tests with provided confiuration.
        Args:
            run_name: name of the run
            repo_url: repository url
            tier: tier of project
            python_version: [py39, py37]
            logs_link: links to logs

        Return:
            _run_python_tests def
        """
        return self._run_python_tests(
            run_name=run_name,
            repo_url=repo_url,
            tier=tier,
            python_version=python_version,
            test_type=TestType.STANDARD,
            logs_link=logs_link,
        )

    def fetch_and_update_main_tests_results(self):
        """Gets executed results from Github actions runs of main repositories."""
        main_repos = self.dao.get_repos_by_tier(Tier.MAIN)
        repo_to_url_mapping = {r.name: r.url for r in main_repos}

        qiskit_dev_version = get_dev_qiskit_version()
        qiskit_stable_version = get_stable_qiskit_version()

        data = [
            # repo, workflow_name, qiskit_version, test_type
            (
                "qiskit-nature",
                "Nature%20Unit%20Tests",
                qiskit_dev_version,
                TestType.DEV_COMPATIBLE,
            ),
            (
                "qiskit-finance",
                "Finance%20Unit%20Tests",
                qiskit_dev_version,
                TestType.DEV_COMPATIBLE,
            ),
            (
                "qiskit-optimization",
                "Optimization%20Unit%20Tests",
                qiskit_dev_version,
                TestType.DEV_COMPATIBLE,
            ),
            (
                "qiskit-machine-learning",
                "Machine%20Learning%20Unit%20Tests",
                qiskit_dev_version,
                TestType.DEV_COMPATIBLE,
            ),
            ("qiskit-experiments", "Tests", qiskit_stable_version, TestType.STANDARD),
            ("qiskit-aer", "Tests%20Linux", qiskit_stable_version, TestType.STANDARD),
        ]

        for repo, workflow_name, qiskit_version, test_type in data:
            self.logger.info("Updating %s repository...", repo)
            _, results = RepositoryActionStatusRunner(
                repo=repo, test_name=workflow_name, qiskit_version=qiskit_version
            ).workload()
            test_result = TestResult(
                passed=all(r.ok for r in results),
                package=Package.QISKIT,
                package_version=qiskit_version,
                test_type=test_type,
            )
            try:
                self.dao.add_repo_test_result(
                    repo_url=repo_to_url_mapping.get(repo),
                    test_result=test_result,
                )
            except KeyError:
                self.logger.warning(
                    "Test result was not saved. There is not repo for url %s",
                    repo,
                )
            self.logger.info("Test results for %s: %s", repo, test_result)
