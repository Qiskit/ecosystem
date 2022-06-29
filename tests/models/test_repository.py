"""Tests for entities."""
import unittest
from datetime import datetime
from pprint import pprint

from ecosystem.models import (
    TestResult,
    TestType,
    RepositoryConfiguration,
    PythonLanguageConfiguration,
)
from ecosystem.models.repository import Repository
from ecosystem.models.test_results import Framework


class TestRepository(unittest.TestCase):
    """Tests repository class."""

    def test_test_results_serialization(self):
        """Tests TestResult class serialization."""
        timestamp = datetime.now().timestamp()
        test_result = TestResult(
            passed=True,
            test_type=TestType.DEV_COMPATIBLE,
            framework=Framework.TERRA,
            framework_version="0.18.1",
            logs_link="log_link",
        )
        test_result.timestamp = timestamp
        expecting = {
            "test_type": "DEV_COMPATIBLE",
            "passed": True,
            "framework": "qiskit-terra",
            "framework_version": "0.18.1",
            "terra_version": "0.18.1",
            "timestamp": timestamp,
            "logs_link": "log_link",
        }

        self.assertEqual(test_result.to_dict(), expecting)

    def test_serialization(self):
        """Tests json serialization.
        Function: Repository
                -> from_dict
        """
        configuration = RepositoryConfiguration(
            language=PythonLanguageConfiguration(versions=["3.6"]),
            dependencies_files=["requirements.txt", "requirements-dev.txt"],
            extra_dependencies=["qiskit"],
            tests_command=["python -m unittest -v"],
            styles_check_command=["pylint -rn ecosystem tests"],
            coverages_check_command=[
                "coverage3 -m pytest",
                "coverage3 report --fail-under=80",
            ],
        )
        main_repo = Repository(
            name="mock-qiskit-terra",
            url="https://github.com/MockQiskit/mock-qiskit.terra",
            description="Mock description for repo.",
            licence="Apache 2.0",
            labels=["mock", "tests"],
            tests_results=[
                TestResult(
                    passed=True,
                    test_type=TestType.DEV_COMPATIBLE,
                    framework=Framework.TERRA,
                    framework_version="0.18.1",
                    logs_link="log_link",
                )
            ],
            configuration=configuration,
            skip_tests=True,
        )
        repo_dict = main_repo.to_dict()
        recovered = Repository.from_dict(repo_dict)
        pprint(repo_dict)
        self.assertEqual(main_repo, recovered)
        self.assertEqual(main_repo.tests_results, recovered.tests_results)
        self.assertEqual(recovered.tests_results[0].logs_link, "log_link")
        # check configs
        self.assertEqual(
            main_repo.configuration.language.name, recovered.configuration.language.name
        )
        self.assertEqual(
            main_repo.configuration.language.versions,
            recovered.configuration.language.versions,
        )
        self.assertEqual(
            main_repo.configuration.tests_command, recovered.configuration.tests_command
        )
        self.assertEqual(
            main_repo.configuration.dependencies_files,
            recovered.configuration.dependencies_files,
        )
        self.assertEqual(
            main_repo.configuration.extra_dependencies,
            recovered.configuration.extra_dependencies,
        )
        self.assertEqual(
            main_repo.configuration.styles_check_command,
            recovered.configuration.styles_check_command,
        )
        self.assertEqual(
            main_repo.configuration.coverages_check_command,
            recovered.configuration.coverages_check_command,
        )
        self.assertTrue(recovered.skip_tests)
