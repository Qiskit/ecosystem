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


#handler = logging.StreamHandler()
#formatter = coloredlogs.ColoredFormatter(fmt='%(asctime)s,%(msecs)03d %(name)s[%(process)d] %(levelname)s %(message)s')
#handler.setFormatter(formatter)
#logger = logging.getLogger()
logger = logging.getLogger('ecosystem')
coloredlogs.DEFAULT_FIELD_STYLES = {
            'name': {'color': 'magenta'},
            'levelname': {'color': 'black', 'bold': True},
            'asctime': {'color': 'green'}}
coloredlogs.install(fmt='%(asctime)s %(name)s %(levelname)s %(message)s',logger=logger)


