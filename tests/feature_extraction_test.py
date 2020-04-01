#!/usr/bin/env python

# First party modules
import hwrt.features as features
import tests.testhelper as testhelper

# from hwrt.handwritten_data import HandwrittenData


def test_feature_detection():
    queue = [
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
    feature_list = features.get_features(queue)
    # TODO: Not only compare lengths of lists but actual contents.
    assert len(feature_list) == len(correct)


def test_repr_and_str():
    algorithms = [
        features.ConstantPointCoordinates(),
        features.FirstNPoints(),
        features.StrokeCount(),
        features.Ink(),
    ]
    for algorithm in algorithms:
        str(algorithm)
        repr(algorithm)


def test_dimension():
    algorithms = [
        (features.ConstantPointCoordinates(), 160),
        (features.FirstNPoints(), 162),  # TODO: Check
        (features.StrokeCount(), 1),
        (features.Ink(), 1),
    ]
    for algorithm, dimension in algorithms:
        assert algorithm.get_dimension() == dimension


def test_height():
    feature_list = [features.Height()]
    a = testhelper.get_symbol_as_handwriting(97705)
    # TODO: Check if this is correct
    assert a.feature_extraction(feature_list) == [263.0]


def test_stroke_count():
    feature_list = [features.StrokeCount()]
    a = testhelper.get_symbol_as_handwriting(97705)
    assert a.feature_extraction(feature_list) == [1]
