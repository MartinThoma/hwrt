#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tests.testhelper as testhelper

# hwrt modules
import hwrt.analyze_data as analyze_data
import hwrt.features as features


# Tests
def execution_test():
    analyze_data.filter_label("\\dag", replace_by_similar=True)
    analyze_data.filter_label("\\diameter", replace_by_similar=True)
    analyze_data.filter_label("\\degree", replace_by_similar=True)
    analyze_data.filter_label("\\alpha", replace_by_similar=True)

    raw_datasets = testhelper.get_raw_datasets()
    feature = features.AspectRatio()
    filename = "aspect_ratio.csv"
    analyze_data.analyze_feature(raw_datasets, feature, filename)


def parser_test():
    analyze_data.get_parser()
