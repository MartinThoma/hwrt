#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import nose

from nose.plugins.skip import SkipTest

# hwrt modules
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
def features_detection_test():
    feature_queue = [{'StrokeCount': None},
                     {'ConstantPointCoordinates': [{'strokes': 4,
                                                    'points_per_stroke': 20,
                                                    'fill_empty_with': 0}]}]
    correct = [features.StrokeCount(),
               features.ConstantPointCoordinates(strokes=4,
                                                 points_per_stroke=20,
                                                 fill_empty_with=0)]
    feature_list = features.get_features(feature_queue)
    # TODO: Not only compare lengths of lists but actual contents.
    nose.tools.assert_equal(len(feature_list), len(correct))


def dimensionality_test():
    feature_list = [(features.StrokeCount(), 1),
                    (features.ConstantPointCoordinates(strokes=4,
                                                       points_per_stroke=20,
                                                       fill_empty_with=0),
                     160),
                    (features.ConstantPointCoordinates(strokes=0,
                                                       points_per_stroke=20,
                                                       fill_empty_with=0), 60),
                    (features.ConstantPointCoordinates(strokes=0,
                                                       points_per_stroke=20,
                                                       pen_down=False), 40),
                    (features.AspectRatio(), 1),
                    (features.Width(), 1),
                    (features.Height(), 1),
                    (features.Time(), 1),
                    (features.CenterOfMass(), 2)
                    ]
    for feat, dimension in feature_list:
        nose.tools.assert_equal(feat.get_dimension(), dimension)


def unknown_class_test():
    # TODO: Test if logging works
    features.get_class("not_existant")


def simple_execution_test():
    algorithms = [features.ConstantPointCoordinates(),
                  features.ConstantPointCoordinates(strokes=0),
                  features.FirstNPoints(),
                  # features.Bitmap(),
                  features.Ink(),
                  features.AspectRatio(),
                  features.Width(),
                  features.Time(),
                  features.CenterOfMass(),
                  features.StrokeCenter(),
                  features.StrokeCenter(8),
                  features.StrokeIntersections(),
                  features.ReCurvature()
                  ]
    for algorithm in algorithms:
        recording = get_symbol_as_handwriting(292934)
        algorithm(recording)


def stroke_intersection1_test():
    """A '&' has one stroke. This stroke intersects itself once."""
    recording = get_symbol_as_handwriting(97705)
    feature = features.StrokeIntersections(1)
    nose.tools.assert_equal(feature(recording), [2])


@SkipTest
def stroke_intersection2_test():
    """A 't' has two strokes. They don't intersect themselves, but they
       intersect once."""
    recording = get_symbol_as_handwriting(293035)
    feature = features.StrokeIntersections(2)
    nose.tools.assert_equal(feature(recording), [0, 1, 0])


def recurvature_test():
    """A 'o' ends in itself. The re-curvature is therefore 0."""
    recording = get_symbol_as_handwriting(293036)
    feature = features.ReCurvature(1)
    nose.tools.assert_equal(feature(recording), [1])
