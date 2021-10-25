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
    
    def get_error_logs(self) -> List[str]:
        """Return warning messages."""
        return [log for log in self.logs if "error" in log.lower()]
    
    def get_fail_logs(self) -> List[str]:
        """Return warning messages."""
        return [log for log in self.logs if "fail" in log.lower()]

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
