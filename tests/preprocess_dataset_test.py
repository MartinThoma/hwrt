#!/usr/bin/env python

# Core Library modules
import os
import shutil

# Third party modules
import pytest

# First party modules
import hwrt.preprocess_dataset as preprocess_dataset
import hwrt.preprocessing as preprocessing
import hwrt.utils as utils


# Tests
@pytest.mark.skip
def test_execution():
    # TODO: nose.proxy.UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80
    #                                      in position 0: invalid start byte
    small = os.path.join(utils.get_project_root(), "preprocessed/small-baseline")
    preprocess_dataset.main(small)


def test_dataset_preparation():
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


def test_get_parameters():
    # TODO: nose.proxy.UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80
    #                                      in position 0: invalid start byte
    small = os.path.join(utils.get_project_root(), "preprocessed/small-baseline")
    preprocess_dataset.get_parameters(small)
