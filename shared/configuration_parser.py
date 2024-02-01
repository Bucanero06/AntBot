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
from os import path

from shared.logging import setup_logger
from shared.string_dict_utils import load_json_file, recursively_normalize_dict_keys, validate_and_correct_dictionary

logger = setup_logger(__name__.split('.')[-1])
DEFAULT_CONFIG_CONTENT = {}

def parse_configuration_file(config_file_path=None):
    """
    Parses a configuration file and returns a dictionary with the configuration.

    If a configuration file path is provided and the file exists, it will be used to load the configuration.
    If the provided file path does not exist, or if no path is provided, a default configuration file will be created
    and a warning message will be logged.

    :param config_file_path: The path to the configuration file. Default is None.
    :type config_file_path: str, optional
    :return: A dictionary representing the configuration.
    :rtype: dict
    :raises AssertionError: If the configuration file cannot be loaded.

    Usage::

        config = parse_configuration_file('config.json')  # Load configuration from 'config.json'
    """
    load_user_configuration = config_file_path and path.isfile(config_file_path)

    if load_user_configuration:
        logger.info(f'Found {config_file_path}')
    else:
        logger.warning(
            f'{config_file_path if config_file_path else "No configuration file"} found. '
            f'Making default configuration file with name {config_file_path}. '
            'Check/Edit configuration file before running.'
        )
        write_example_configuration_file(config_file_path)
    #
    config = load_json_file(config_file_path if load_user_configuration else config_file_path)
    config = recursively_normalize_dict_keys(config)

    default_config = recursively_normalize_dict_keys(DEFAULT_CONFIG_CONTENT)
    config, log = validate_and_correct_dictionary(config, default_config)

    for message in log:
        logger.warning(message)

    assert config, f'Could not load configuration file {config_file_path}'
    from pprint import pformat
    logger.debug(f'Configuration:\n{pformat(config)}')
    return config


def write_example_configuration_file(file_name: str, DEFAULT_CONFIG_CONTENT=None):
    """
    Writes an example configuration file.

    This function creates a configuration file with default settings in the current working directory.
    If a file name is not provided, it uses a default name.

    :param file_name: The name of the file to be created.
    :type file_name: str, optional
    :raises Exception: Logs an error if the example configuration file cannot be written.

    Usage::

        write_example_configuration_file('example_config.json') # Creates 'example_config.json' with default settings
    """

    try:
        #Make sure it is a json file
        if not file_name.endswith('.json'):
            file_name += '.json'
            logger.warning(f'File name {file_name} does not end with .json. Appending .json to file name.')
        # Write Configuration FIle with Defaults
        with open(file_name, 'w') as configfile:
            json.dump(DEFAULT_CONFIG_CONTENT, configfile, indent=4)
        logger.info(f'Wrote example configuration file {file_name}')
    except Exception as e:
        logger.error(f'Could not write example configuration file {file_name}')
        logger.error(e)
