"""Tests for shell commands."""
import os

from ecosystem.commands import CloneRepoCommand, ShellCommand
from ecosystem.models import CommandExecutionSummary
from tests.common import TestCaseWithResources


class TestCommands(TestCaseWithResources):
    """Tests for shell commands methods."""

    def test_execute_command(self):
        """Tests command execution:
        Function: ShellCommand 
                -> execute
        """
        execution_result = ShellCommand.execute(
            ["ls", "-al"], directory=os.path.dirname(os.path.abspath(__file__))
        )
        self.assertTrue(isinstance(execution_result, CommandExecutionSummary))
        self.assertTrue(len(execution_result.logs) > 0)

    def test_clone_repo(self):
        """Tests repo cloning:
        Function: CloneRepoCommand 
                -> execute
        """
        clone_res = CloneRepoCommand.execute(
            repo="https://github.com/octocat/Hello-World", directory=self.path
        )
        self.assertTrue(os.path.exists(f"{self.path}/Hello-World"))
        self.assertEqual(clone_res.code, 0)
