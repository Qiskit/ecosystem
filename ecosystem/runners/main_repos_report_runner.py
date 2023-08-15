"""Runner for reports on main repositories."""
from typing import Tuple, List, Union

from .runner import Runner
from ..models import CommandExecutionSummary
from ..models.repository import Repository
from ..utils.custom_requests import get_workflow_status


class RepositoryActionStatusRunner(Runner):
    """Runner to get information from CI tests from repository."""

    def __init__(
        self, repo: Union[str, Repository], test_name: str, qiskit_version: str
    ):
        super().__init__(repo)
        self.test_name = test_name
        self.qiskit_version = qiskit_version

    def workload(self) -> Tuple[str, List[CommandExecutionSummary]]:
        status = get_workflow_status(repo=self.repo, name_of_workflow=self.test_name)
        return self.qiskit_version, [
            CommandExecutionSummary(code=int(not status), logs=[])
        ]
