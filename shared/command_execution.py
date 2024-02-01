#! /usr/bin/env python3.10
# Copyright (c) 2024 Carbonyl LLC & Carbonyl R&D
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import json
import sys
from subprocess import Popen, PIPE, CalledProcessError

from shared.logging import setup_logger

logger = setup_logger(__name__.split('.')[-1])


# todo i want to be able to pass a re output handler for user defined parsing
def execute_command(command: str, write_stream=True, _logger=None) -> (int, list, list):
    """
    Execute a shell command and capture the standard output and standard error streams.

    :param command: The shell command to execute.
    :type command: str
    :param write_stream: Flag indicating whether to write the output streams to the log, defaults to True.
    :type write_stream: bool, optional
    :param _logger: A logger instance to use for logging, defaults to None, in which case the global `logger` is used.
    :type _logger: logging.Logger, optional
    :return: The return code of the command, and the standard output and standard error captured as lists.
    :rtype: tuple(int, list, list)
    :raises CalledProcessError: If the command returns a non-zero exit status.
    """
    if _logger is None:
        _logger = logger

    _logger.info(f"Executing command: {command}")
    stdout_output_list = []
    stderr_output_list = []
    try:
        with Popen(command, stdout=PIPE, stderr=PIPE, bufsize=1, universal_newlines=True, shell=True) as p:
            for line in p.stdout:
                line = line.strip()
                stdout_output_list.append(line)
                if write_stream:
                    _logger.info(line)
            for line in p.stderr:
                line = line.strip()
                stderr_output_list.append(line)
                if write_stream:
                    _logger.error(line)
        return_code = p.returncode

        stdout_output_list, stderr_output_list = json.dumps(stdout_output_list), json.dumps(stderr_output_list)
        if return_code != 0:
            raise CalledProcessError(return_code, p.args, output=stdout_output_list,
                                     stderr=stderr_output_list)

        return return_code, json.loads(stdout_output_list), json.loads(stderr_output_list)

    except Exception as e:
        raise e



