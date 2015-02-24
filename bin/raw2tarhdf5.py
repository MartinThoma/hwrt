#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Convert a raw datafile to a tar with HDF5 files."""

import numpy as np

from base64 import b64encode, b64decode
from StringIO import StringIO
import yaml
import h5py
import tarfile
import os
import csv
import pickle

# hwrt modules
import hwrt.utils as utils


def get_parser():
    """Return the parser object for this script."""
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--input",
                        dest="raw_file",
                        help="where is the raw data file (.pickle)?",
                        metavar="FILE")
    return parser


def main(raw_file):
    data = pickle.load(open(raw_file, "rb"))
    handwriting_datasets = data['handwriting_datasets']
    formula_id2latex = data['formula_id2latex']


if __name__ == '__main__':
    args = get_parser().parse_args()
    main(args.raw_file)
