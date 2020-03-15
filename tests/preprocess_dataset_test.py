#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Core Library modules
import os
import shutil

# Third party modules
import nose

# First party modules
import hwrt.preprocess_dataset as preprocess_dataset
import hwrt.preprocessing as preprocessing
import hwrt.utils as utils


# Tests
@nose.tools.nottest
def execution_test():
    # TODO: nose.proxy.UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80
    #                                      in position 0: invalid start byte
    small = os.path.join(utils.get_project_root(), "preprocessed/small-baseline")
    preprocess_dataset.main(small)


def dataset_preparation_test():
    d = os.path.dirname(__file__)
    target = os.path.join(
        utils.get_project_root(), "raw-datasets/unittests-tiny-raw.pickle"
    )
    shutil.copyfile(os.path.join(d, "data/unittests-tiny-raw.pickle"), target)
    preprocess_dataset.create_preprocessed_dataset(
        target,
        os.path.join(
            utils.get_project_root(), "preprocessed/small-baseline/data.pickle"
        ),
        [preprocessing.ScaleAndShift()],
    )


def get_parameters_test():
    # TODO: nose.proxy.UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80
    #                                      in position 0: invalid start byte
    small = os.path.join(utils.get_project_root(), "preprocessed/small-baseline")
    preprocess_dataset.get_parameters(small)
