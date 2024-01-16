#! /usr/bin/env python3.10
import json

from shared.logging import setup_logger

logger = setup_logger(__name__.split('.')[-1])


def remove_spaces_and_set_case(key: str, case='lower') -> str:
    """
    Normalize a string key by converting all characters to lowercase
    and removing all spaces and underscores.

    :param key: The string key to be normalized.
    :type key: str
    :return: The normalized key.
    :rtype: str

    Usage::

        normalized_key = normalize_key('Hello_World')
        print(normalized_key)  # Output: 'helloworld'
    """
    assert case in ['lower', 'l', 'u', 'upper'], "Case must be either 'lower' or 'upper'"

    translation_table = str.maketrans('', '', ' _')
    if case in ['lower', 'l']:
        return key.lower().translate(translation_table)
    else:
        return key.upper().translate(translation_table)


def recursively_normalize_dict_keys(d: dict) -> dict:
    """
    Normalize all keys in a dictionary. If a value is a dictionary,
    normalize its keys recursively.

    :param d: The dictionary whose keys are to be normalized.
    :type d: dict
    :return: A new dictionary with normalized keys.
    :rtype: dict

    Usage::

        data = {
            'Hello World': 1,
            'Good_Day': {
                'Inner_Key': 2
            }
        }
        normalized_data = normalize_dict(data)
        print(normalized_data)  # Output: {'helloworld': 1, 'goodday': {'innerkey': 2}}
    """
    return {
        remove_spaces_and_set_case(key): recursively_normalize_dict_keys(value) if isinstance(value,
                                                                                              dict) else value
        for key, value in d.items()
    }


def validate_and_correct_dictionary(dict_to_verify: dict, default_config: dict, log=None) -> tuple:
    """
    Verifies that the given JSON config contains all the required keys as per the default config.
    If not, adds the missing keys with the default values.
    Returns a log of warnings and errors in case of missing or unknown keys.

    :param dict_to_verify: The JSON configuration to verify.
    :type dict_to_verify: dict
    :param default_config: The default configuration used for verification.
    :type default_config: dict
    :param log: A list of log messages. Default is an empty list.
    :type log: list, optional
    :return: A tuple of the verified JSON configuration and the log of warnings/errors.
    :rtype: tuple

    Usage::

        json_config = {
            "key1": "value1",
            "key2": {
                "subkey1": "subvalue1"
            }
        }

        default_config = {
            "key1": "value1",
            "key2": {
                "subkey1": "subvalue1",
                "subkey2": "subvalue2"
            },
            "key3": "value3"
        }

        verified_config, log = verify_configuration_keys(json_config, default_config)
        # verified_config will contain all keys from default_config, and log will contain warning/error messages
    """
    if log is None:
        log = []
    if not dict_to_verify:
        dict_to_verify = {}

    for key, value in default_config.items():
        if key not in dict_to_verify:
            dict_to_verify[key] = value
            log.append(f'Warning: Missing key "{key}" has been added with default value "{value}"')
        elif isinstance(value, dict):
            if isinstance(dict_to_verify[key], dict):
                dict_to_verify[key], log = validate_and_correct_dictionary(dict_to_verify[key], value, log)
            else:
                log.append(f'Error: Key "{key}" should contain a dictionary but found "{type(dict_to_verify[key])}"')
        else:
            if not isinstance(dict_to_verify[key], type(value)):
                log.append(
                    f'Error: Key "{key}" should be of type "{type(value)}" but found "{type(dict_to_verify[key])}"')

    for key in dict_to_verify.keys():
        if key not in default_config:
            log.append(f'Error: Unknown key "{key}" found in config')

    return dict_to_verify, log


def remove_json_comments(json_string):
    """
    Removes the comments from a JSON string.

    :param json_string: The JSON string.
    :type json_string: str
    :return: The cleaned JSON string.
    :rtype: str
    """
    lines = json_string.split("\n")
    cleaned_lines = [line.split("//")[0] for line in lines]
    cleaned_json = "\n".join(cleaned_lines)
    return cleaned_json


def load_json_file(filename):
    """
    Loads a JSON file.

    :param filename: The path to the JSON file.
    :type filename: str
    :return: The content of the JSON file.
    :rtype: dict
    """
    assert filename.endswith(".json") or filename.endswith(".JSON"), "File must be a JSON file"
    with open(filename, 'r') as f:
        cleaned_json = remove_json_comments(f.read())
        return json.loads(cleaned_json)


def save_json_file(filename, data):
    """
    Saves a JSON file.

    :param filename: The path to the JSON file.
    :param data: The data to be saved.
    :type filename: str
    :type data: dict
    """
    assert filename.endswith(".json") or filename.endswith(".JSON"), "File must be a JSON file"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
