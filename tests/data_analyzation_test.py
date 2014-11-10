#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import nose

# hwrt modules
from hwrt.HandwrittenData import HandwrittenData
import hwrt.data_analyzation_metrics as dam


# Test helper
def get_all_symbols():
    current_folder = os.path.dirname(os.path.realpath(__file__))
    symbol_folder = os.path.join(current_folder, "symbols")
    symbols = [os.path.join(symbol_folder, f)
               for f in os.listdir(symbol_folder)
               if os.path.isfile(os.path.join(symbol_folder, f))]
    return symbols


def get_raw_datasets():
    raw_datasets = []
    for hwr in get_all_symbols_as_handwriting():
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


def get_all_symbols_as_handwriting():
    handwritings = []
    for symbol_file in get_all_symbols():
        with open(symbol_file) as f:
            data = f.read()
        handwritings.append(HandwrittenData(data))
    return handwritings


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


# Tests
def get_class_test():
    nose.tools.assert_equal(dam.get_class('Creator'), dam.Creator)


def get_metrics_test():
    d = [{'Creator': None}, {'Creator': [{'filename': 'bla'}]}]
    metrics = dam.get_metrics(d)
    nose.tools.assert_equal(len(metrics), 2)


def unknown_class_test():
    # TODO: Test if logging works
    dam.get_class("not_existant")


def execution_test():
    raw_datasets = get_raw_datasets()
    l = [dam.Creator(), dam.InstrokeSpeed(), dam.InterStrokeDistance(),
         dam.TimeBetweenPointsAndStrokes()]
    for alg in l:
        alg(raw_datasets)
