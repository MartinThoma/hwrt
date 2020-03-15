#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Convert a raw datafile to a tar with HDF5 files."""

# Core Library modules
import csv
import os
import pickle
import tarfile
from base64 import b64decode, b64encode
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

# Third party modules
import numpy as np
import yaml

# First party modules
import h5py
# hwrt modules
import hwrt.utils as utils


def get_parser():
    """Return the parser object for this script."""
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

    parser = ArgumentParser(
        description=__doc__, formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-i",
        "--input",
        dest="raw_file",
        help="where is the raw data file (.pickle)?",
        metavar="FILE",
    )
    return parser


def main(raw_file):
    data = pickle.load(open(raw_file, "rb"))
    handwriting_datasets = data["handwriting_datasets"]
    formula_id2latex = data["formula_id2latex"]


if __name__ == "__main__":
    args = get_parser().parse_args()
    main(args.raw_file)
