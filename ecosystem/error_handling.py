# This code is part of Qiskit.
#
# (C) Copyright IBM 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Logging module."""

import os
import logging
from typing import Tuple, List, Union
import coloredlogs


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


def set_actions_output(outputs: List[Tuple[str, Union[str, bool, float, int]]]) -> None:
    """Sets output for GitHub actions.

    Args:
        outputs: List of pairs:
            - first element - name of output
            - second element - value of output
    """
    for name, value in outputs:
        logger.info("Setting output variable %s: %s", name, value)
        if value is not None:
            assert "\n" not in value, f"Error: Newlines in github output ({value})"
        if "CI" in os.environ:
            with open(os.environ["GITHUB_OUTPUT"], "a") as github_env:
                github_env.write(f"{name}={value}\n")
        else:
            # Used only during unit tests
            print(f"{name}={value}")


class EcosystemError(Exception):
    """Base class for Ecosystem exceptions."""

    def __init__(self, message: str, logger_level=None):
        super().__init__(message)
        if logger_level is None:
            logger_level = logger.error
        logger_level(message)
        self.message = message
