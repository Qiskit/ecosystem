"""Tests for shell commands."""
import os

from ecosystem.commands import _execute_command, _clone_repo
from ecosystem.entities import CommandExecutionSummary
from .common import TestCaseWithResources


class TestCommands(TestCaseWithResources):
    """Tests shell commands."""

    def test_execute_command(self):
        """Tests command execution."""
        execution_result = _execute_command(["ls", "-al"],
                                            cwd=os.path.dirname(os.path.abspath(__file__)))
        self.assertTrue(isinstance(execution_result, CommandExecutionSummary))
        self.assertTrue(len(execution_result.logs) > 0)

    def test_clone_repo(self):
        """Tests repo cloning."""
        clone_res = _clone_repo("https://github.com/octocat/Hello-World",
                                directory=self.path)
        self.assertTrue(os.path.exists(f"{self.path}/Hello-World"))
        self.assertEqual(clone_res.code, 0)
