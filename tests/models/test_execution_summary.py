"""Tests for execution summary class."""

from unittest import TestCase

from ecosystem.models import CommandExecutionSummary


class TestExecutionSummary(TestCase):
    """Tests for execution summary class."""

    def test_qiskit_deprecation_warning_detection(self):
        """Tests detection of qiskit deprecation logs."""

        deprecation_log_message = (
            "/usr/local/"
            "lib/python3.8/site-packages/qiskit/terra/__init__.py:86"
            ": DeprecationWarning: The QuantumCircuit.combine() method is being deprecated."
            "Use the compose() method which is more flexible"
            "w.r.t circuit register compatibility."
        )

        summary_with_qiskit_deprecation = CommandExecutionSummary(
            code=0, logs=[deprecation_log_message]
        )

        self.assertTrue(summary_with_qiskit_deprecation.has_qiskit_deprecation_logs)

        clear_summary = CommandExecutionSummary(code=0, logs=[])

        self.assertFalse(clear_summary.has_qiskit_deprecation_logs)
