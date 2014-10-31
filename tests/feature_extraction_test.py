#!/usr/bin/env python

import os
import nose
# mine
from hwrt.HandwrittenData import HandwrittenData
import hwrt.preprocessing as preprocessing
import hwrt.features as features


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
def feature_detection_test():
    l = [{'StrokeCount': None},
         {'ConstantPointCoordinates':
          [{'strokes': 4},
           {'points_per_stroke': 81},
           {'fill_empty_with': 0},
           {'pen_down': False}]
          }
         ]
    correct = [features.StrokeCount(),
               features.ConstantPointCoordinates(strokes=4,
                                                 points_per_stroke=81,
                                                 fill_empty_with=0,
                                                 pen_down=False)]
    feature_list = features.get_features(l)
    # TODO: Not only compare lengths of lists but actual contents.
    nose.tools.assert_equal(len(feature_list), len(correct))


def unknown_class_test():
    # TODO: Test if logging works
    features.get_class("not_existant")


def repr_and_str_test():
    l = [features.ConstantPointCoordinates(),
         features.FirstNPoints(),
         features.StrokeCount(),
         features.Bitmap(),
         features.Ink()
         ]
    for alg in l:
        alg.__str__()
        alg.__repr__()


def dimension_test():
    l = [(features.ConstantPointCoordinates(), 160),
         (features.FirstNPoints(), 162),  # TODO: Check
         (features.StrokeCount(), 1),
         (features.Bitmap(), 784),
         (features.Ink(), 1)
         ]
    for alg, dimension in l:
        nose.tools.assert_equal(alg.get_dimension(), dimension)


def height_test():
    feature_list = [features.Height()]
    a = get_symbol_as_handwriting(97705)
    # TODO: Check if this is correct
    nose.tools.assert_equal(a.feature_extraction(feature_list), [263.0])


def stroke_count_test():
    feature_list = [features.StrokeCount()]
    a = get_symbol_as_handwriting(97705)
    nose.tools.assert_equal(a.feature_extraction(feature_list), [1])
