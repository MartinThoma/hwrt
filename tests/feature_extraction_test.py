#!/usr/bin/env python
# -*- coding: utf-8 -*-

import nose
import tests.testhelper as testhelper

# hwrt modules
from hwrt.HandwrittenData import HandwrittenData
import hwrt.preprocessing as preprocessing
import hwrt.features as features


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


def repr_and_str_test():
    l = [features.ConstantPointCoordinates(),
         features.FirstNPoints(),
         features.StrokeCount(),
         features.Ink()
         ]
    for alg in l:
        str(alg)
        repr(alg)


def dimension_test():
    l = [(features.ConstantPointCoordinates(), 160),
         (features.FirstNPoints(), 162),  # TODO: Check
         (features.StrokeCount(), 1),
         (features.Ink(), 1)
         ]
    for alg, dimension in l:
        nose.tools.assert_equal(alg.get_dimension(), dimension)


def height_test():
    feature_list = [features.Height()]
    a = testhelper.get_symbol_as_handwriting(97705)
    # TODO: Check if this is correct
    nose.tools.assert_equal(a.feature_extraction(feature_list), [263.0])


def stroke_count_test():
    feature_list = [features.StrokeCount()]
    a = testhelper.get_symbol_as_handwriting(97705)
    nose.tools.assert_equal(a.feature_extraction(feature_list), [1])
