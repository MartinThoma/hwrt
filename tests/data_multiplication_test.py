#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import nose

# hwrt modules
from hwrt.HandwrittenData import HandwrittenData
import hwrt.preprocessing as preprocessing
import hwrt.features as features
import hwrt.data_multiplication as data_multiplication


# Test helper
def get_all_symbols():
    current_folder = os.path.dirname(os.path.realpath(__file__))
    symbol_folder = os.path.join(current_folder, "symbols")
    symbols = [os.path.join(symbol_folder, f)
               for f in os.listdir(symbol_folder)
               if os.path.isfile(os.path.join(symbol_folder, f))]
    return symbols


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
def data_multiplication_detection_test():
    l = [{'Multiply': None},
         {'Multiply': [{'nr': 1}]},
         {'Rotate':
          [{'minimum': -3},
           {'maximum': +3},
           {'num': 3}]
          }
         ]
    correct = [data_multiplication.Multiply(nr=1),
               data_multiplication.Multiply(nr=1),
               data_multiplication.Rotate(minimum=-3,
                                          maximum=3,
                                          num=3)]
    mult_queue = data_multiplication.get_data_multiplication_queue(l)
    # TODO: Not only compare lengths of lists but actual contents.
    nose.tools.assert_equal(len(mult_queue), len(correct))


def unknown_class_test():
    # TODO: Test if logging works
    data_multiplication.get_class("not_existant")


def rotate_test():
    recording = get_symbol_as_handwriting(292934)
    rotation = data_multiplication.Rotate(minimum=-3, maximum=3, num=3)
    new_recordings = rotation(recording)
    # TODO: Not only compare lengths of lists but actual contents.
    nose.tools.assert_equal(len(new_recordings), 3)
