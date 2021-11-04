"""Execution summary model."""
from typing import List, Optional


class CommandExecutionSummary:
    """Utils for command execution results."""

    def __init__(
        self,
        code: int,
        logs: List[str],
        summary: Optional[str] = None,
        name: Optional[str] = None,
    ):
        """CommandExecutionSummary class."""
        self.name = name or ""
        self.code = code
        self.logs = logs
        if summary:
            self.summary = summary
        elif len(self.logs) > 0:
            self.summary = "".join(self.logs[-3:])
        else:
            self.summary = summary

    def get_warning_logs(self) -> List[str]:
        """Return warning messages."""
        return [log for log in self.logs if "warn" in log.lower()]

    def get_qiskit_depreciation_logs(self) -> List[str]:
        """Return qiskit depreciation messages."""
        return [
            log
            for log in self.logs
            if "qiskit" in log.lower() and "DeprecationWarning" in log
        ]

    def get_error_logs(self) -> List[str]:
        """Return error messages."""
        return [log for log in self.logs if "error" in log.lower()]

    def get_fail_logs(self) -> List[str]:
        """Return fail messages."""
        return [log for log in self.logs if "failed" in log.lower()]

    @property
    def has_qiskit_deprecation_logs(self) -> bool:
        """Wether execution summary has deprecation warnings for Qiskit or not."""
        qiskit_deprecation_logs = [
            log
            for log in self.logs
            if "qiskit" in log.lower() and "DeprecationWarning" in log
        ]
        return len(qiskit_deprecation_logs) > 0

    @property
    def ok(self):  # pylint: disable=invalid-name
        """If command finished with success."""
        return self.code == 0

    @classmethod
    def empty(cls) -> "CommandExecutionSummary":
        """Returns empty summary."""
        return cls(0, [])

    def __repr__(self):
        return (
            f"CommandExecutionSummary({self.name} | code: {self.code} | {self.summary})"
        )
