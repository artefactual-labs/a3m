"""
A Job is MCP Client's representation of a unit of work to be
performed--corresponding to a Task on the MCP Server side.  Jobs are run in
batches by clientScript modules and populated with an exit code, standard out
and standard error information.
"""
import logging
import os
import sys
import traceback
from contextlib import contextmanager


STANDARD_FORMAT = (
    "%(levelname)-8s  %(asctime)s  %(name)s.%(funcName)s:%(lineno)d  %(message)s"
)

SCRIPT_FILE_FORMAT = "{}: %(levelname)-8s  %(asctime)s  %(name)s:%(funcName)s:%(lineno)d:  %(message)s".format(
    os.path.basename(sys.argv[0])
)


class CallbackHandler(logging.Handler):
    def __init__(self, callback, module_name=None):
        logging.Handler.__init__(self)
        fmt = STANDARD_FORMAT if module_name else SCRIPT_FILE_FORMAT
        self.formatter = logging.Formatter(f"{module_name}: {fmt}")
        self.callback = callback

    def emit(self, record):
        self.callback(self.format(record))


class Job:
    def __init__(self, name, uuid, args, caller_wants_output=False):
        self.name = name
        self.UUID = uuid
        self.args = [name] + args
        self.caller_wants_output = caller_wants_output
        self.int_code = 0
        self.status_code = "success"
        self.output = ""
        self.error = ""

    def dump(self):
        return (
            "\n\n\t| =============== JOB\n"
            "\t| %s (exit=%s; code=%s uuid=%s)\n"
            "\t| =============== STDOUT\n"
            "\t| %s\n"
            "\t| =============== END STDOUT\n"
            "\t| =============== STDERR\n"
            "\t| %s\n"
            "\t| =============== END STDERR\n"
            "\t| =============== ARGS\n"
            "\t| %s\n"
            "\t| =============== END ARGS\n"
        ) % (
            self.name,
            self.int_code,
            self.status_code,
            self.UUID,
            self.get_stdout(),
            self.get_stderr(),
            self.args,
        )

    def set_status(self, int_code, status_code="success"):
        if int_code:
            self.int_code = int(int_code)
        self.status_code = status_code

    def write_output(self, s):
        self.output += s

    def write_error(self, s):
        self.error += s

    def print_output(self, *args):
        self.write_output(" ".join([self._to_str(x) for x in args]) + "\n")

    def print_error(self, *args):
        self.write_error(" ".join([self._to_str(x) for x in args]) + "\n")

    @staticmethod
    def _to_str(thing):
        try:
            return str(thing)
        except UnicodeEncodeError:
            return thing.encode("utf8")

    def pyprint(self, *objects, **kwargs):
        file = kwargs.get("file", sys.stdout)
        sep = kwargs.get("sep", " ")
        end = kwargs.get("end", "\n")
        msg = sep.join([self._to_str(x) for x in objects]) + end
        if file == sys.stdout:
            self.write_output(msg)
        elif file == sys.stderr:
            self.write_error(msg)
        else:
            raise Exception("Unrecognised print file: " + str(file))

    def get_exit_code(self):
        return self.int_code

    def get_stdout(self):
        return self.output

    def get_stderr(self):
        return self.error

    @contextmanager
    def JobContext(self, logger=None):
        handler = CallbackHandler(self.print_error, self.name)

        if logger:
            logger.addHandler(handler)

        try:
            yield
        except Exception as e:
            self.write_error(str(e))
            self.write_error(traceback.format_exc())
            self.set_status(1)
        finally:
            if logger:
                logger.removeHandler(handler)
