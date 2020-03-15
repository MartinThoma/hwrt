#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Core Library modules
import os
import shutil

# Third party modules
import nose

# First party modules
import hwrt.data_analyzation_metrics as dam
import hwrt.utils as utils
import tests.testhelper as testhelper
from hwrt.handwritten_data import HandwrittenData


# Tests
def get_metrics_test():
    d = [{"Creator": None}, {"Creator": [{"filename": "create_test.csv"}]}]
    metrics = dam.get_metrics(d)
    nose.tools.assert_equal(len(metrics), 2)


def execution_test():
    raw_datasets = testhelper.get_raw_datasets()
    l = [
        dam.Creator(),
        dam.InstrokeSpeed(),
        dam.InterStrokeDistance(),
        dam.TimeBetweenPointsAndStrokes(),
        dam.AnalyzeErrors(),
    ]
    for alg in l:
        alg(raw_datasets)


def execution_test2():
    d = os.path.dirname(__file__)
    raw_datasets = os.path.join(
        utils.get_project_root(), "raw-datasets/unittests-tiny-raw.pickle"
    )
    shutil.copyfile(os.path.join(d, "data/unittests-tiny-raw.pickle"), raw_datasets)
    dam.TimeBetweenPointsAndStrokes(raw_datasets)
