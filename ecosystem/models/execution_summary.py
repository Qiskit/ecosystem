"""Execution summary model."""
from __future__ import annotations


class CommandExecutionSummary:
    """Utils for command execution results."""

    def __init__(
        self,
        code: int,
        logs: list[str],
        summary: str | None = None,
        name: str | None = None,
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

    def get_warning_logs(self) -> list[str]:
        """Return warning messages."""
        return [log for log in self.logs if "warn" in log.lower()]

    def get_qiskit_depreciation_logs(self) -> list[str]:
        """Return qiskit depreciation messages."""
        return [
            log
            for log in self.logs
            if "qiskit" in log.lower()
            and "DeprecationWarning" in log
            and "qiskit.aqua" not in log.lower()
        ]

    def get_error_logs(self) -> list[str]:
        """Return error messages."""
        return [log for log in self.logs if "error" in log.lower()]

    def get_fail_logs(self) -> list[str]:
        """Return fail messages."""
        return [log for log in self.logs if "failed" in log.lower()]

    @property
    def has_qiskit_deprecation_logs(self) -> bool:
        """Wether execution summary has deprecation warnings for Qiskit or not."""
        qiskit_deprecation_logs = self.get_qiskit_depreciation_logs()
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
