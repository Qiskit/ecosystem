"""Tests for execution summary class."""

from unittest import TestCase

from ecosystem.models import CommandExecutionSummary


class TestExecutionSummary(TestCase):
    """Tests for execution summary class."""

    def test_qiskit_deprecation_warning_detection(self):
        """Tests detection of qiskit deprecation logs.
        Function: CommandExecutionSummary
                -> has_qiskit_deprecation_logs
        """

        deprecation_log_message = (
            "/srv/conda/envs/notebook/"
            "lib/python3.8/site-packages/qiskit/aqua/__init__.py:86"
            ": DeprecationWarning: The package qiskit.aqua is deprecated."
            " It was moved/refactored to qiskit-terra For more"
            " information see <https://github.com/Qiskit"
            "/qiskit-aqua/blob/main/README.md#migration-guide>"
            " warn_package('aqua', 'qiskit-terra')"
        )

        summary_with_qiskit_deprecation = CommandExecutionSummary(
            code=0, logs=[deprecation_log_message]
        )

        self.assertTrue(summary_with_qiskit_deprecation.has_qiskit_deprecation_logs)

        clear_summary = CommandExecutionSummary(code=0, logs=[])

        self.assertFalse(clear_summary.has_qiskit_deprecation_logs)
