#!/usr/bin/env python
# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import annotations

import io
import os
import shlex
import subprocess  # nosec B404
import sys
import tempfile
from typing import Any
from typing import Union

from a3m.fpr.registry import CommandScriptType


ExecutionResult = tuple[int, str, str]
StandardInputType = Union[str, bytes, io.IOBase]
SubprocessCommand = Union[str, list[str]]


def launchSubProcess(
    command: SubprocessCommand,
    stdIn: StandardInputType = "",
    printing: bool = False,
    arguments: list = [],
    env_updates: dict = {},
    capture_output: bool = False,
) -> ExecutionResult:
    """
    Launches a subprocess using ``command``, where ``command`` is either:
    a) a single string containing a commandline statement, or
    b) an array of commands and parameters.

    In the former case, ``command`` is first split via shlex.split() before
    being executed. No subshell will be used in either case; the commands are
    directly execed.

    Keyword arguments:
    stdIn:      A string which will be fed as standard input to the executed
                process, or a file object which will be provided as a stream
                to the process being executed.
                Default is an empty string.
    printing:   Boolean which controls whether the subprocess's output is
                printed to standard output. Default is True.
    arguments:  An array of arguments to pass to ``command``. Note that this is
                only honoured if ``command`` is an array, and will be ignored
                if ``command`` is a string.
    env_updates: Dict of changes to apply to the started process' environment.
    capture_output: Whether or not to capture stdout from the subprocess.
                    Defaults to `False`. If `False`, then stdout is never
                    captured and is returned as an empty string; if `True`,
                    then stdout is always captured. The stderr is always
                    captured from the subprocess, regardless of this setting.
                    If `capture_output` is `False`, then that stderr is only
                    returned IF the subprocess has failed, i.e., returned a
                    non-zero exit code.
    """
    # These represent subprocess output so we use bytes until they're returned
    stdError = b""
    stdOut = b""

    try:
        # Split command strings but pass through arrays untouched
        if isinstance(command, str):
            command = shlex.split(command)
        else:
            command.extend(arguments)

        my_env = os.environ.copy()
        my_env["PYTHONIOENCODING"] = "utf-8"
        if "LANG" not in my_env or not my_env["LANG"]:
            my_env["LANG"] = "en_US.UTF-8"
        if "LANGUAGE" not in my_env or not my_env["LANGUAGE"]:
            my_env["LANGUAGE"] = my_env["LANG"]
        my_env.update(env_updates)

        stdin_pipe: Any
        communicate_input: bytes | None
        if isinstance(stdIn, str):
            stdin_pipe = subprocess.PIPE
            communicate_input = stdIn.encode()
        elif isinstance(stdIn, bytes):
            stdin_pipe = subprocess.PIPE
            communicate_input = stdIn
        elif isinstance(stdIn, io.IOBase):
            stdin_pipe = stdIn
            communicate_input = None
        else:
            raise Exception(f"stdIn must be a string or a file object ({type(stdIn)}).")
        if capture_output:
            # Capture the stdout and stderr of the subprocess
            p = subprocess.Popen(  # nosec B603
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=stdin_pipe,
                env=my_env,
            )
            stdOut, stdError = p.communicate(input=communicate_input)
        else:
            # Ignore the stdout of the subprocess, capturing only stderr
            with open(os.devnull, "w") as devnull:
                p = subprocess.Popen(  # nosec B603
                    command,
                    stdin=stdin_pipe,
                    env=my_env,
                    stdout=devnull,
                    stderr=subprocess.PIPE,
                )
                __, stdError = p.communicate(input=communicate_input)
        retcode = p.returncode
        # If we are not capturing output and the subprocess has succeeded, set
        # its stderr to the empty string.
        if (not capture_output) and (retcode == 0):
            stdError = b""
        # append the output to stderror and stdout
        if printing:
            print(stdOut.decode("utf8"))
            print(stdError.decode("utf8"), file=sys.stderr)
    except OSError as ose:
        print("Execution failed:", ose, file=sys.stderr)
        return -1, "Config Error!", ose.__str__()
    except Exception as inst:
        print("Execution failed:", command, file=sys.stderr)
        print(type(inst), file=sys.stderr)  # the exception instance
        print(inst.args, file=sys.stderr)
        return -1, "Execution failed:", " ".join(command)
    return retcode, stdOut.decode("utf8"), stdError.decode("utf8")


def createAndRunScript(
    command: SubprocessCommand,
    printing: bool = False,
    arguments: list = [],
    env_updates: dict = {},
    capture_output: bool = True,
):
    with tempfile.NamedTemporaryFile(
        encoding="utf-8", mode="wt", delete=False
    ) as tmpfile:
        os.chmod(tmpfile.name, 0o700)
        if isinstance(command, str):
            tmpfile.write(command)
        else:
            tmpfile.write("".join(command))
        tmpfile.close()
        cmd = [tmpfile.name]
        cmd.extend(arguments)

        # Run it
        ret = launchSubProcess(
            cmd,
            stdIn="",
            printing=printing,
            env_updates=env_updates,
            capture_output=capture_output,
        )
        os.unlink(tmpfile.name)

    return ret


def executeOrRun(
    type: CommandScriptType | str,
    command: SubprocessCommand,
    stdIn: StandardInputType = "",
    printing: bool = False,
    arguments: list = [],
    env_updates: dict = {},
    capture_output: bool = True,
) -> ExecutionResult:
    """
    Attempts to run the provided command on the shell, with the text of
    "stdIn" passed as standard input if provided. The type parameter
    should be one of the following:

    command:    Runs the argument as a direct command line. In this usage,
                "text" should be a complete commandline statement,
                which will be split with shlex.split(), or an array.
    bashScript, pythonScript:
                Interprets the "text" argument as the source code to either
                a bash or python script, as appropriate. The appropriate
                shebang will be prepended, then the script will be written
                to disk and executed. If the "arguments" parameter is passed,
                they will be appended to the array that is built to be
                passed to subprocess.Popen.
    as_is:      Like the above, except that the provided script is executed
                without modification.

    Keyword arguments:
    stdIn:      A string which will be fed as standard input to the executed process.
                Default is empty.
    printing:   Boolean which controls whether the subprocess's output is
                printed to standard output. Default is True.
    arguments:  An array of arguments to pass to ``command``. Note that this is only
                honoured if ``command`` is an array, and will be ignored if ``command``
                is a string.
    env_updates: Dict of changes to apply to the started process' environment.
    capture_output: Whether or not to capture output for the executed process.
                Default is `True`.
    """
    if isinstance(type, str):
        try:
            type = CommandScriptType(type)
        except ValueError:
            raise ValueError(f"unknown type {type}")
    if type == CommandScriptType.COMMAND:
        return launchSubProcess(
            command,
            stdIn=stdIn,
            printing=printing,
            arguments=arguments,
            env_updates=env_updates,
            capture_output=capture_output,
        )
    if type == CommandScriptType.BASH_SCRIPT:
        if not isinstance(command, str):
            raise ValueError("command must be a str")
        command = "#!/bin/bash\n" + command
        return createAndRunScript(
            command,
            printing=printing,
            arguments=arguments,
            env_updates=env_updates,
            capture_output=capture_output,
        )
    if type == CommandScriptType.PYTHON_SCRIPT:
        if not isinstance(command, str):
            raise ValueError("command must be a str")
        command = "#!/usr/bin/env python\n" + command
        return createAndRunScript(
            command,
            printing=printing,
            arguments=arguments,
            env_updates=env_updates,
            capture_output=capture_output,
        )
    if type == CommandScriptType.AS_IS:
        return createAndRunScript(
            command,
            printing=printing,
            arguments=arguments,
            env_updates=env_updates,
            capture_output=capture_output,
        )
    raise ValueError(f"unknown type {type}")
