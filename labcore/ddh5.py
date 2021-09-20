"""plottr.data.datadict_storage

Provides file-storage tools for the DataDict class.

Description of the HDF5 storage format
======================================

We use a simple mapping from DataDict to the HDF5 file. Within the file,
a single DataDict is stored in a (top-level) group of the file.
The data fields are datasets within that group.

Global meta data of the DataDict are attributes of the group; field meta data
are attributes of the dataset (incl., the `unit` and `axes` values). The meta
data keys are given exactly like in the DataDict, i.e., incl the double
underscore pre- and suffix.
"""
import os
import time
from enum import Enum
from typing import Any, Union, Optional, Dict, Type, Collection
from types import TracebackType

import numpy as np
import h5py

from plottr.data.datadict import DataDict, is_meta_key
from plottr.data.datadict_storage import *

from .measurement.sweep import Sweep

__author__ = 'Wolfgang Pfaff'
__license__ = 'MIT'


def _create_datadict_structure(sweep: Sweep) -> DataDict:
    """
    Returns a structured DataDict from the DataSpecs of a Sweep.

    :param sweep: Sweep object from which the DataDict is created.
    """

    data_specs = sweep.get_data_specs()
    data_dict = DataDict()
    for spec in data_specs:

        depends_on = spec.depends_on
        unit = spec.unit
        name = spec.name

        # Checks which fields have information and which ones are None.
        if depends_on is None:
            if unit is None:
                data_dict[name] = dict()
            else:
                data_dict[name] = dict(unit=unit)
        else:
            if unit is None:
                data_dict[name] = dict(axes=depends_on)
            else:
                data_dict[name] = dict(axes=depends_on, unit=unit)

    data_dict.validate()

    return data_dict


def _check_none(line: Dict, all: bool = True) -> bool:
    """
    Checks if the values in a Dict are all None. Returns True if all values are None, False otherwise.
    """
    if all:
        for k, v in line.items():
            if v is None:
                return True
        return False

    if len(set(line.values())) == 1:
        for k, v in line.items():
            if v is None:
                return True
    return False


def run_and_save_sweep(sweep: Sweep, data_dir: str, name: str, ignore_all_None_results: bool = True) -> None:
    """
    Iterates through a sweep, saving the data coming through it into a file called <name> at <data_dir> directory.

    :param sweep: Sweep object to iterate through.
    :param data_dir: Directory of file location
    :param name: name of the file
    :param prt: Bool, if True, the function will print every result coming from the sweep. Default, False.
    """
    data_dict = _create_datadict_structure(sweep)

    # Creates a file even when it fails.
    with DDH5Writer(data_dict, data_dir, name=name) as writer:
        for line in sweep:
            for k, v in line.items():
                try:
                    info = v.shape
                except:
                    info = v
            if not _check_none(line, all=ignore_all_None_results):
                writer.add_data(**line)

    print('The measurement has finished successfully and all of the data has been saved.')
