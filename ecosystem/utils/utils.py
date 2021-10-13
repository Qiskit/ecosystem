"""General logger for ecosystem."""
import logging
import os
from typing import Tuple, List


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


handler = logging.StreamHandler()
formatter = OneLineExceptionFormatter(logging.BASIC_FORMAT)
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(os.environ.get("LOGLEVEL", "INFO"))
logger.addHandler(handler)


def set_actions_output(outputs: List[Tuple[str, str]]) -> None:
    """Sets output for GitHub actions.
    Args:
        outputs: List of pairs:
            - first element - name of output
            - second element - value of output
    """
    for name, value in outputs:
        logger.info("Setting output variable %s: %s", name, value)
        print("::set-output name={name}::{value}".format(name=name, value=value))
