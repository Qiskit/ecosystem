"""Tests for shell commands."""
import os
import shutil
from unittest import TestCase

from ecosystem.shell import _execute_command, _clone_repo
from ecosystem.entities import CommandExecutionSummary


class TestShell(TestCase):
    """Tests shell commands."""
    def setUp(self) -> None:
        self.path = "./resources"
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def tearDown(self) -> None:
        if os.path.exists(self.path):
            shutil.rmtree(self.path)

    def test_execute_command(self):
        """Tests command execution."""
        execution_result = _execute_command(["ls", "-al"])
        self.assertTrue(isinstance(execution_result, CommandExecutionSummary))
        self.assertTrue(len(execution_result.logs) > 0)
        self.assertTrue("test_shell.py" in execution_result.summary)

    def test_clone_repo(self):
        """Tests repo cloning."""
        clone_res = _clone_repo("https://github.com/octocat/Hello-World",
                                directory=self.path)
        self.assertTrue(os.path.exists(f"{self.path}/Hello-World"))
        self.assertEqual(clone_res.code, 0)
