#!/usr/bin/env python
# -*- coding: utf-8 -*-

import nose
import tests.testhelper as testhelper

# hwrt modules
from hwrt.HandwrittenData import HandwrittenData
import hwrt.features as features
import hwrt.preprocessing as preprocessing


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


def print_featurelist_test():
    feature_list = [features.StrokeCount(),
                    features.ConstantPointCoordinates(strokes=4,
                                                      points_per_stroke=20,
                                                      fill_empty_with=0),
                    features.ConstantPointCoordinates(strokes=0,
                                                      points_per_stroke=20,
                                                      fill_empty_with=0),
                    features.ConstantPointCoordinates(strokes=0,
                                                      points_per_stroke=20,
                                                      pen_down=False),
                    features.AspectRatio(),
                    features.Width(),
                    features.Height(),
                    features.Time(),
                    features.CenterOfMass()
                    ]
    features.print_featurelist(feature_list)


def constant_point_coordinates_test():
    f = features.ConstantPointCoordinates(strokes=0,
                                          points_per_stroke=2,
                                          pen_down=False)
    g = features.ConstantPointCoordinates(strokes=0,
                                          points_per_stroke=200,
                                          pen_down=False)
    recording = testhelper.get_symbol_as_handwriting(292934)
    f._features_without_strokes(recording)
    g._features_without_strokes(recording)
    space_evenly = preprocessing.SpaceEvenly()
    space_evenly(recording)
    f._features_without_strokes(recording)


def stroke_intersections_test():
    f = features.StrokeIntersections(strokes=4)
    recording = testhelper.get_symbol_as_handwriting(293035)
    x = f(recording)
    nose.tools.assert_equal(x, [0, 1, 0, 0, 0, 0, 0, 0, 0, 0])


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
        recording = testhelper.get_symbol_as_handwriting(292934)
        algorithm(recording)


def stroke_intersection1_test():
    """A '&' has one stroke. This stroke intersects itself once."""
    recording = testhelper.get_symbol_as_handwriting(97705)
    feature = features.StrokeIntersections(1)
    nose.tools.assert_equal(feature(recording), [2])


def stroke_intersection2_test():
    """A 't' has two strokes. They don't intersect themselves, but they
       intersect once."""
    recording = testhelper.get_symbol_as_handwriting(293035)
    feature = features.StrokeIntersections(2)
    nose.tools.assert_equal(feature(recording), [0, 1, 0])


def recurvature_test():
    """A 'o' ends in itself. The re-curvature is therefore 0."""
    recording = testhelper.get_symbol_as_handwriting(293036)
    feature = features.ReCurvature(1)
    feature(recording)
