#! /usr/bin/env python3.10

import decimal
import re

import h5py as h5py
import numpy as np

from shared.logging import setup_logger

logger = setup_logger(__name__.split('.')[-1])


def extract_datasets_from_h5_to_csv(h5_filepath, dataset_mapping):
    """
    Extract specific datasets from an HDF5 file and save them to CSV files.

    Parameters:
    - h5_filepath: Path to the input HDF5 file.
    - dataset_mapping: Dictionary where keys are dataset names in the HDF5 file
                       and values are the output filenames for CSV files.

    Note:
        - it will flatten the data in the dataset to a 2D array if the dataset is a 3D array
            - 3D arrays of shape (x, y, z) → 2D arrays of shape (x*y, z)
            - 4D arrays of shape (w, x, y, z) → 2D arrays of shape (wxy, z)
            - ... and so on.
    """
    with h5py.File(h5_filepath, 'r') as h5_file:
        for dataset_name, output_file in dataset_mapping.items():
            try:
                if dataset_name in h5_file:
                    logger.debug(f"Extracting dataset {dataset_name} from {h5_filepath} to {output_file}")
                    data = flatten_ND_to_2D(h5_file[dataset_name][:])  # Flatten the data to 2D
                    # Save the data as a CSV file
                    np.savetxt(output_file, data, delimiter=',')
                else:
                    logger.warning(f"Dataset {dataset_name} not found in {h5_filepath}")
            except Exception as e:
                logger.error(f"Error extracting dataset {dataset_name}: {e}")


def flatten_ND_to_2D(array):
    """Flatten a multi-dimensional array keeping the last dimension and format its values."""
    if array.ndim > 1:
        flat = array.reshape(-1, array.shape[-1])  # Flatten all dimensions except the last one
    else:
        flat = array  # If already 1D, no reshaping needed
    return flat


def float_range(start, stop, step):
    """
    A generator function that yields a range of floating point numbers.

    :param start: The start of the range.
    :param stop: The end of the range.
    :param step: The step size.
    :type start: float
    :type stop: float
    :type step: float
    :yields: Each value in the range.
    :rtype: float
    """
    while start < stop:
        yield format(start, '.1f')  # float(start)
        start += decimal.Decimal(step)


def get_dipole_values_as_array(filename, string, delimiter):
    """
    Reads a file and returns the values of a string in the file as an array.

    :param filename: The path to the file.
    :param string: The string to search for.
    :param delimiter: The delimiter that separates the string and its values.
    :type filename: str
    :type string: str
    :type delimiter: str
    :return: The values of the string in the file.
    :rtype: list
    """
    with open(filename, 'r') as fin:
        value = []
        for line in fin:
            if string in line:
                option_value = (line.partition(delimiter)[2]).strip()
                value.append(option_value)
        return value


def natural_sort(iterable, key=None, reverse=False):
    """
    Sorts the given iterable in a natural order.

    This function is a key-function to the built-in `sorted` function and can be
    used as a drop-in replacement for it.

    A natural sort, also known as an alphanumeric sort, is a sorting method that orders strings containing numbers in
    a way that considers the numerical value of the digits rather than treating the entire string as a sequence of
    characters. In other words, it sorts strings with numbers in a way that reflects their numerical order.

    :param iterable: The iterable to be sorted.
    :param key: A callable used to extract a comparison key from each element in the iterable.
    :param reverse: If set to True, the iterable will be sorted in descending order.
    :type iterable: iterable
    :type key: callable, optional
    :type reverse: bool, optional
    :return: A new list containing the sorted elements from the iterable.
    :rtype: list

    Usage::
        >>> natural_sort(['2 ft', '10 ft', '1 ft'])
        ['1 ft', '2 ft', '10 ft']
    """

    def __float_convert(match):
        try:
            return float(match.group())
        except ValueError:
            return match.group()

    if key is None:
        key = lambda x: x
    else:
        key = lambda x: (__float_convert(match) for match in re.finditer(r'\d+|\D+', key(x)))

    return sorted(iterable, key=key, reverse=reverse)
