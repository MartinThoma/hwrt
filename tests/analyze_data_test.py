#!/usr/bin/env python

# First party modules
import hwrt.analyze_data as analyze_data
import hwrt.features as features
import tests.testhelper as testhelper


def test_execution():
    """
    Test if analyze_data.filter_label and analyze_data.analyze_feature are
    executable at all.
    """
    analyze_data.filter_label("\\dag", replace_by_similar=True)
    analyze_data.filter_label("\\diameter", replace_by_similar=True)
    analyze_data.filter_label("\\degree", replace_by_similar=True)
    analyze_data.filter_label("\\alpha", replace_by_similar=True)

    raw_datasets = testhelper.get_raw_datasets()
    feature = features.AspectRatio()
    filename = "aspect_ratio.csv"
    analyze_data.analyze_feature(raw_datasets, feature, filename)
