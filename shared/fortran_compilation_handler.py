"""This code is defined in Python, specifically intended to facilitate the process of compiling Fortran code. It
provides logging facilities to capture any errors or warnings that may occur during the compilation process. It
contains two key methods:

1. `process_compiler_output(output: str)`: This function is used to parse the output of the Fortran compiler to
identify errors and warnings, and log them in a more readable format. It does this by looping over each line of the
output, using a regular expression to extract relevant information, and then storing the errors and warnings in
defaultdict objects.

2. `compile_fortran_code(directory: str, make_flags: str = '')`: This function is used to compile the Fortran code in
the given directory and handle any errors or warnings. It changes to the given directory, compiles the code,
and then changes back to the original directory. If any errors are encountered during the process, they are logged
and further processed by `process_compiler_output(output: str)` function.

This code also imports various modules for usage:

- `os`: To interact with the OS, specifically for changing directories and getting current working directory. - `re`:
For regular expressions. - `defaultdict`: A type of Python's built-in dictionary that allows you to specify a default
value for keys that have not yet been assigned a value. - `CalledProcessError`: A specific type of Python error,
raised when a process run by the subprocess module (or by the command line) returns a non-zero exit status. -
`execute_command`: A custom function from a local module to execute a shell command. - `setup_logger`: A custom
function from a local module to set up a logger for capturing and handling log messages.

The imported `setup_logger` function is used to create a logger, which is then used within these functions to log any
relevant information, such as successful compilation, or any errors or warnings that may have occurred.

Note: This is a fairly advanced script, and it assumes a certain file structure and that certain utilities (like a
'make' command and a proper setup Makefile) are available in the directory. The script also assumes the presence of
certain locally defined modules (`densitypy.project_utils.def_functions.execute_command` and
`densitypy.project_utils.logger.setup_logger`).

"""

import os
import re
from collections import defaultdict
from subprocess import CalledProcessError

import pandas as pd



logger = setup_logger("compiler")
import json


def print_in_human_readable_format(stdout_list, remarks, warnings, errors, others):
    """
    Print logs in a human-readable format. It logs the compiler output, remarks, warnings, errors, and others.

    :param stdout_list: List of standard output messages from the compiler.
    :type stdout_list: list
    :param remarks: Dictionary containing remarks from the compiler.
    :type remarks: dict
    :param warnings: Dictionary containing warnings from the compiler.
    :type warnings: dict
    :param errors: Dictionary containing errors from the compiler.
    :type errors: dict
    :param others: Dictionary containing other logs from the compiler.
    :type others: dict
    """

    logger.info(">>>>>>>>>Make Output<<<<<<<<<")

    if stdout_list:
        for line in stdout_list:
            logger.info(f"{line}")

    if remarks:
        for file_path, remark_list in remarks.items():
            logger.remarks(f"------File: {file_path}------")
            for line_number, message_type, code, message, variable, code_reference in remark_list:
                logger.remarks(f" Line {line_number} [{variable}]:{code} {message}")
            logger.remarks("-----------------------------")

    if warnings:
        for file_path, warning_list in warnings.items():
            logger.warning(f"------File: {file_path}------")
            for line_number, message_type, code, message, variable, code_reference in warning_list:
                logger.warning(f" Line {line_number} [{variable}]:{code} {message}")
            logger.warning("-----------------------------")

    if others:
        for file_path, others_list in others.items():
            for line_number, message_type, code, message, variable, code_reference in others_list:
                logger.unknown(f"{message}")

    if errors:
        for file_path, error_list in errors.items():
            logger.error(f"------File: {file_path}------")
            for line_number, message_type, code, message, variable, code_reference in error_list:
                logger.error(f" Line {line_number} [{variable}]:{code} {message}")
            logger.error("-----------------------------")

    logger.info(">>>>>End of Make Output<<<<<")


def process_compiler_output(stdout_list: list, stderr_list: list, return_levels: bool = False):
    """
    Process the output of the compiler and store errors, warnings, and remarks in separate dictionaries.

    :param stdout_list: List of standard output messages from the compiler.
    :type stdout_list: list
    :param stderr_list: List of standard error messages from the compiler.
    :type stderr_list: list
    :param return_levels: Flag indicating whether to return errors, warnings, remarks, and others separately, defaults to False.
    :type return_levels: bool, optional
    :return: Dataframe containing processed output of the compiler or tuple containing errors, warnings, remarks, others, and the dataframe based on `return_levels`.
    :rtype: pd.DataFrame or tuple
    """
    # Dictionaries to store errors, warnings, remarks, and others
    errors = defaultdict(list)
    warnings = defaultdict(list)
    remarks = defaultdict(list)
    others = defaultdict(list)

    # Create an empty list to store the dictionaries
    data_list = []

    # regex pattern to match error, warning, and remark messages
    pattern = r"^(.+)\((\d+)\):\s+(.+?)\s+#(\d+):\s+(.+?)\.\s+\[(.+?)\]"
    DUMMY_LINE_COUNTER = None

    for index, line in enumerate(stderr_list):
        match = re.match(pattern, line)
        if match:
            DUMMY_LINE_COUNTER = 0

            file_path, line_number, message_type, code, message, variable = match.groups()
            line_number = int(line_number)
            code = int(code)
            code_reference = stderr_list[index + 1]
            message_type = message_type.upper()
            # Save match into appropriate category
            if "WARNING" in message_type:
                warnings[file_path].append((line_number, message_type, code, message, variable, code_reference))
            elif "ERROR" in message_type:
                errors[file_path].append((line_number, message_type, code, message, variable, code_reference))
            elif "REMARKS" in message_type:
                remarks[file_path].append((line_number, message_type, code, message, variable, code_reference))
        else:
            if DUMMY_LINE_COUNTER == 0:
                DUMMY_LINE_COUNTER = 1
            elif DUMMY_LINE_COUNTER == 1:
                pass
            else:
                DUMMY_LINE_COUNTER = None
                # save lines which don't match the pattern in others
                file_path, line_number, message_type, code, message, variable, code_reference = 'Unknown', pd.NA, 'other', pd.NA, line, 'Unknown', 'Unknown'
                others[file_path].append((line_number, message_type, code, message, variable, code_reference))

        if DUMMY_LINE_COUNTER != 1:
            # Append the extracted data as a dictionary to the list
            data_list.append({
                'File': file_path,
                'Line_Number': line_number,
                'Type': message_type,
                'Code': code,
                'Message': message,
                'Variable': variable,
                'Code_Reference': code_reference
            })

    # Create the DataFrame from the list of dictionaries
    df = pd.DataFrame(data_list)

    # Sort the DataFrame by line number (with -1 values moved to the bottom)
    df = df.sort_values(by=['Line_Number'], ascending=True, na_position='last').astype(
        {'Line_Number': 'Int64', 'Code': 'Int64'})
    df = df.reset_index(drop=True)

    # Print output in human-readable format
    print_in_human_readable_format(stdout_list=stdout_list, remarks=remarks, warnings=warnings, errors=errors,
                                   others=others)

    # Return appropriate output based on flag
    if return_levels:
        return errors, warnings, remarks, others, df
    else:
        return df


def compile_ifort_fortran_code(directory: str, make_flags: str = ''):
    """
    Compile Fortran code using Intel Fortran compiler (ifort). It processes the compilation output to identify and log
    errors, warnings, and remarks.

    :param directory: Directory containing the Fortran code to be compiled.
    :type directory: str
    :param make_flags: Flags to be passed to the 'make' command, defaults to empty string.
    :type make_flags: str, optional
    :return: Return code of the compilation process and a dataframe containing processed output of the compiler.
    :rtype: tuple
    """
    # Check ifort is installed
    try:
        return_code, stdout_output_list, stderr_output_list = \
            execute_command(f"ifort --version", write_stream=False)
        logger.info(f"{stdout_output_list[0]} is installed.")
    except CalledProcessError as e:
        logger.error(f"ifort does not seem to be installed. Please install ifort and try again."
                     f"Error: {e}")
        return e.returncode, None
    # Use the given directory and get the exact path needed to not cause any errors
    directory = os.path.abspath(directory)
    # Compile the code and handle any potential errors
    try:
        # Compile the code and capture output and remarks/warnings/errors/others
        return_code, stdout_output_list, stderr_output_list = \
            execute_command(f"make -C {directory} {make_flags}", write_stream=True)
        # Process the output and return the errors, warnings, remarks, and others
        compilation_output_df = process_compiler_output(stdout_output_list, stderr_output_list)

        return return_code, compilation_output_df


    except CalledProcessError as e:
        # Process the output and return the errors, warnings, remarks, and others
        compilation_output_df = process_compiler_output(json.loads(e.stdout), json.loads(e.stderr))
        logger.error(f"Compilation failed with return code {e.returncode}.")

        return e.returncode, compilation_output_df
