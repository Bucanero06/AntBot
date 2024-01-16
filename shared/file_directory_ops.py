#! /usr/bin/env python3.10
import os
import shutil
import sys
from contextlib import contextmanager
from os import path

from shared.command_execution import execute_command
from shared.logging import setup_logger

logger = setup_logger(__name__.split('.')[-1])


@contextmanager
def change_directory(new_directory):
    """Context manager to change the working directory temporarily."""
    current_directory = os.getcwd()
    os.chdir(new_directory)
    try:
        yield
    finally:
        os.chdir(current_directory)


class change_directory_manager:
    def __init__(self, new_dir):
        self.new_dir = new_dir
        self.original_dir = os.getcwd()

    def __enter__(self):
        os.chdir(self.new_dir)

    def __exit__(self, type, value, traceback):
        os.chdir(self.original_dir)


def copy_to(input, output, include_directories=True):
    """
    Copies a file to a new location.

    :param input: The path of the file to be copied.
    :param output: The path to copy the file to.
    :type input: str
    :type output: str
    """

    cp_flags = '-r' if include_directories else ''
    try:
        logger.info(f"Copying: {input} to {output}")
        execute_command(f'cp {cp_flags} {input} {output}')
    except Exception as e:
        logger.info("Error copying file: " + str(e))


def delete_files_or_directories(*paths, ignore_errors=False):
    """
    Deletes the files or directories specified by the given paths.

    :param paths: The paths of files or directories to be deleted.
    :type paths: str
    :raises FileNotFoundError: If the given path does not exist.

    Usage::

        delete_files_or_directories('/path/to/file', '/path/to/directory')  # Deletes specified file and directory
    """
    for paths in paths:
        try:
            if os.path.isfile(paths):
                os.remove(paths)  # Delete the file
            elif os.path.isdir(paths):
                shutil.rmtree(paths)  # Delete the directory and its contents
            else:
                if not ignore_errors:
                    raise FileNotFoundError(f"Path '{paths}' does not exist.")
        except Exception as e:
            if ignore_errors:
                logger.warning(f"Error deleting file or directory: {e}")
            else:
                logger.error(f"Error deleting file or directory: {e}")
                raise e


def find(filename, *args):
    """
    Searches for a file in multiple directories.

    :param filename: The name of the file to search for.
    :param args: The directories to search in.
    :type filename: str
    :type args: str
    :return: The first directory where the file was found.
    :rtype: str
    """
    directories = [*args]
    foundfile = False
    for searchdirectory in directories:
        if path.exists(searchdirectory + "/" + filename):
            if searchdirectory == ".":
                logger.info(f"Found {filename} inside the current directory")
            else:
                logger.info(f"Found {filename} inside {searchdirectory} directory")
            foundfile = True
            return searchdirectory
    # if not exited by now it means that the file was not found in any of the given directories thus rise error
    if foundfile != True:
        logger.info(f'{filename} not found inside {directories} directories')
        logger.info("exiting...")
        sys.exit()


def file_len(file_path):
    """
    Returns the number of lines in a file.

    :param file_path: The path to the file.
    :type file_path: str
    :return: The number of lines in the file.
    :rtype: int
    """
    with open(file_path) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


def file_lenth(filename):
    """
    Returns the number of lines in a file.

    :param filename: The path to the file.
    :type filename: str
    :return: The number of lines in the file.
    :rtype: int
    """
    with open(filename) as fin:
        for i, l in enumerate(fin):
            pass
    return i + 1


def get_all_files_in_directory(directory):
    """
    Returns all files in a directory.

    :param directory: The path to the directory.
    :type directory: str
    :return: All files in the directory.
    :rtype: list
    """
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]


def get_folders_in_directory(directory):
    """
    Returns the folders in a directory.

    :param directory: The path to the directory.
    :type directory: str
    :return: The folders in the directory.
    :rtype: list
    """
    return [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]


def make_directory(output_dir: str, delete_if_exists: bool = False):
    """
    Creates a directory at the specified path. If the directory already exists and 'delete_if_exists' is True,
    it deletes the existing directory before creating a new one.

    :param output_dir: The path where the directory is to be created.
    :type output_dir: str
    :param delete_if_exists: If True, deletes the directory at 'output_dir' if it exists. Default is False.
    :type delete_if_exists: bool

    Usage::

        make_directory('/path/to/directory', delete_if_exists=True)  # Creates directory, deleting existing one if necessary
    """
    if delete_if_exists and os.path.exists(output_dir):  delete_files_or_directories(output_dir)
    os.makedirs(output_dir, exist_ok=True)  # Create the directory


def uniquify(filepath):
    """
    Makes a file path unique by appending a counter to the file name.

    :param filepath: The initial file path.
    :type filepath: str
    :return: A unique file path.
    :rtype: str
    """
    filename, extension = path.splitext(filepath)
    logger.info(filename, extension)
    counter = 1

    while path.exists(filepath):
        filepath = f'{filename}_{counter}{extension}'
        logger.info(counter)
        counter += 1

    return filepath


def validate_directory_and_get_full_path(path):
    path = path.strip()
    if not os.path.exists(path):
        raise ValueError(f'{path} does not exist.')
    if not os.path.isdir(path):
        raise ValueError(f'{path} is not a directory.')
    return os.path.abspath(path)
