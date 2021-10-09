import logging,coloredlogs 
import os


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
logger = logging.getLogger('ecosystem')
coloredlogs.install(level='INFO', logger=logger)