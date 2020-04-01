#!/usr/bin/env python

# Core Library modules
import os
import shutil

# First party modules
import hwrt.data_analyzation_metrics as dam
import hwrt.utils as utils
import tests.testhelper as testhelper


def test_get_metrics_test():
    d = [{"Creator": None}, {"Creator": [{"filename": "create_test.csv"}]}]
    metrics = dam.get_metrics(d)
    assert len(metrics) == 2


def test_execution_test():
    raw_datasets = testhelper.get_raw_datasets()
    algorithms = [
        dam.Creator(),
        dam.InstrokeSpeed(),
        dam.InterStrokeDistance(),
        dam.TimeBetweenPointsAndStrokes(),
        dam.AnalyzeErrors(),
    ]
    for algorithm in algorithms:
        algorithm(raw_datasets)


def test_execution_test2():
    d = os.path.dirname(__file__)
    raw_datasets = os.path.join(
        utils.get_project_root(), "raw-datasets/unittests-tiny-raw.pickle"
    )
    shutil.copyfile(os.path.join(d, "data/unittests-tiny-raw.pickle"), raw_datasets)
    dam.TimeBetweenPointsAndStrokes(raw_datasets)
