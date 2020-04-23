import logging.config
import logging.handlers
import os
import sys


class CallbackHandler(logging.Handler):
    def __init__(self, callback, module_name=None):
        logging.Handler.__init__(self)
        self.formatter = logging.Formatter(
            f"{module_name}: " + STANDARD_FORMAT if module_name else SCRIPT_FILE_FORMAT
        )
        self.callback = callback

    def emit(self, record):
        self.callback(self.format(record))


STANDARD_FORMAT = (
    "%(levelname)-8s  %(asctime)s  %(name)s.%(funcName)s:%(lineno)d  %(message)s"
)
SCRIPT_FILE_FORMAT = "{}: %(levelname)-8s  %(asctime)s  %(name)s:%(funcName)s:%(lineno)d:  %(message)s".format(
    os.path.basename(sys.argv[0])
)


def get_script_logger(name):
    return logging.getLogger(name)
