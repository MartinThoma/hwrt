#!/usr/bin/env python
# -*- coding: utf-8 -*-

import nose
import os

# hwrt modules
import hwrt.analyze_data as analyze_data
import hwrt.features as features
from hwrt.HandwrittenData import HandwrittenData


# Test helper
def get_all_symbols():
    current_folder = os.path.dirname(os.path.realpath(__file__))
    symbol_folder = os.path.join(current_folder, "symbols")
    symbols = [os.path.join(symbol_folder, f)
               for f in os.listdir(symbol_folder)
               if os.path.isfile(os.path.join(symbol_folder, f))]
    return symbols


def get_all_symbols_as_handwriting():
    handwritings = []
    for symbol_file in get_all_symbols():
        with open(symbol_file) as f:
            data = f.read()
        handwritings.append(HandwrittenData(data))
    return handwritings


def get_raw_datasets():
    raw_datasets = []
    for hwr in get_all_symbols_as_handwriting():
        hwr.formula_in_latex = 'TESTHELPER'
        hwr.formula_id = 42
        hwr.raw_data_id = 1337
        raw_datasets.append({'is_in_testset': 0,
                             'formula_id': hwr.formula_id,
                             'handwriting': hwr,
                             'formula_in_latex': hwr.formula_in_latex,
                             'id': hwr.raw_data_id})
    return raw_datasets


# Tests
def execution_test():
    analyze_data.filter_label("\\dag", replace_by_similar=True)
    analyze_data.filter_label("\\diameter", replace_by_similar=True)
    analyze_data.filter_label("\\degree", replace_by_similar=True)
    analyze_data.filter_label("\\alpha", replace_by_similar=True)

    raw_datasets = get_raw_datasets()
    feature = features.AspectRatio()
    filename = "aspect_ratio.csv"
    analyze_data.analyze_feature(raw_datasets, feature, filename)


def parser_test():
    analyze_data.get_parser()
