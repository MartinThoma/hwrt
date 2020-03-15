#!/usr/bin/env python
# -*- coding: utf-8 -*-

# First party modules
import hwrt.features as features
import tests.testhelper as testhelper
from hwrt.handwritten_data import HandwrittenData


def test_feature_detection():
    l = [
        {"StrokeCount": None},
        {
            "ConstantPointCoordinates": [
                {"strokes": 4},
                {"points_per_stroke": 81},
                {"fill_empty_with": 0},
                {"pen_down": False},
            ]
        },
    ]
    correct = [
        features.StrokeCount(),
        features.ConstantPointCoordinates(
            strokes=4, points_per_stroke=81, fill_empty_with=0, pen_down=False
        ),
    ]
    feature_list = features.get_features(l)
    # TODO: Not only compare lengths of lists but actual contents.
    assert len(feature_list) == len(correct)


def test_repr_and_str():
    l = [
        features.ConstantPointCoordinates(),
        features.FirstNPoints(),
        features.StrokeCount(),
        features.Ink(),
    ]
    for alg in l:
        str(alg)
        repr(alg)


def test_dimension():
    l = [
        (features.ConstantPointCoordinates(), 160),
        (features.FirstNPoints(), 162),  # TODO: Check
        (features.StrokeCount(), 1),
        (features.Ink(), 1),
    ]
    for alg, dimension in l:
        assert alg.get_dimension() == dimension


def test_height():
    feature_list = [features.Height()]
    a = testhelper.get_symbol_as_handwriting(97705)
    # TODO: Check if this is correct
    assert a.feature_extraction(feature_list) == [263.0]


def test_stroke_count():
    feature_list = [features.StrokeCount()]
    a = testhelper.get_symbol_as_handwriting(97705)
    assert a.feature_extraction(feature_list) == [1]
