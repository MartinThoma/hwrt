#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Helper functions for tests."""

import os

# hwrt modules
from hwrt.HandwrittenData import HandwrittenData


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


def get_symbol(raw_data_id):
    current_folder = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(current_folder, "symbols/%i.json" % raw_data_id)
    return file_path


def get_symbol_as_handwriting(raw_data_id):
    symbol_file = get_symbol(raw_data_id)
    with open(symbol_file) as f:
        data = f.read()
    a = HandwrittenData(data)
    return a


def compare_pointlists(a, b, epsilon=0.001):
    """Check if two stroke lists (a and b) are equal."""
    if len(a) != len(b):
        return False
    for stroke_a, stroke_b in zip(a, b):
        if len(stroke_a) != len(stroke_b):
            return False
        for point_a, point_b in zip(stroke_a, stroke_b):
            keys = ['x', 'y', 'time']
            for key in keys:
                if abs(point_a[key] - point_b[key]) > epsilon:
                    return False
    return True
