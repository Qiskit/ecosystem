"""Logging module."""
import logging
import coloredlogs


class QiskitEcosystemException(Exception):
    """Exceptions for qiskit ecosystem."""


class OneLineExceptionFormatter(logging.Formatter):
    """Exception formatter"""

    def formatException(self, ei):
        result = super().formatException(ei)
        return repr(result)

    def format(self, record):
        result = super().format(record)
        if record.exc_text:
            result = result.replace("\n", "")
        return result


logger = logging.getLogger("ecosystem")
coloredlogs.DEFAULT_FIELD_STYLES = {
    "name": {"color": "magenta"},
    "levelname": {"color": "black", "bold": True},
    "asctime": {"color": "black", "bold": True},
}
coloredlogs.install(fmt="%(asctime)s %(name)s %(levelname)s %(message)s", logger=logger)
