#!/usr/bin/env python

# First party modules
import hwrt.features as features
import hwrt.preprocessing as preprocessing
import tests.testhelper as testhelper


def test_features_detection():
    feature_queue = [
        {"StrokeCount": None},
        {
            "ConstantPointCoordinates": [
                {"strokes": 4, "points_per_stroke": 20, "fill_empty_with": 0}
            ]
        },
    ]
    correct = [
        features.StrokeCount(),
        features.ConstantPointCoordinates(
            strokes=4, points_per_stroke=20, fill_empty_with=0
        ),
    ]
    feature_list = features.get_features(feature_queue)
    # TODO: Not only compare lengths of lists but actual contents.
    assert len(feature_list) == len(correct)


def test_print_featurelist():
    """Test features.print_featurelist."""
    feature_list = [
        features.StrokeCount(),
        features.ConstantPointCoordinates(
            strokes=4, points_per_stroke=20, fill_empty_with=0
        ),
        features.ConstantPointCoordinates(
            strokes=0, points_per_stroke=20, fill_empty_with=0
        ),
        features.ConstantPointCoordinates(
            strokes=0, points_per_stroke=20, pen_down=False
        ),
        features.AspectRatio(),
        features.Width(),
        features.Height(),
        features.Time(),
        features.CenterOfMass(),
    ]
    features.print_featurelist(feature_list)


def test_constant_point_coordinates():
    """Test features.ConstantPointCoordinates."""
    f = features.ConstantPointCoordinates(
        strokes=0, points_per_stroke=2, pen_down=False
    )
    g = features.ConstantPointCoordinates(
        strokes=0, points_per_stroke=200, pen_down=False
    )
    recording = testhelper.get_symbol_as_handwriting(292934)
    f._features_without_strokes(recording)
    g._features_without_strokes(recording)
    space_evenly = preprocessing.SpaceEvenly()
    space_evenly(recording)
    f._features_without_strokes(recording)


def test_stroke_intersections():
    f = features.StrokeIntersections(strokes=4)
    recording = testhelper.get_symbol_as_handwriting(293035)
    x = f(recording)
    assert x == [0, 1, 0, 0, 0, 0, 0, 0, 0, 0]


def test_dimensionality():
    feature_list = [
        (features.StrokeCount(), 1),
        (
            features.ConstantPointCoordinates(
                strokes=4, points_per_stroke=20, fill_empty_with=0
            ),
            160,
        ),
        (
            features.ConstantPointCoordinates(
                strokes=0, points_per_stroke=20, fill_empty_with=0
            ),
            60,
        ),
        (
            features.ConstantPointCoordinates(
                strokes=0, points_per_stroke=20, pen_down=False
            ),
            40,
        ),
        (features.AspectRatio(), 1),
        (features.Width(), 1),
        (features.Height(), 1),
        (features.Time(), 1),
        (features.CenterOfMass(), 2),
    ]
    for feat, dimension in feature_list:
        assert feat.get_dimension() == dimension


def test_simple_execution():
    algorithms = [
        features.ConstantPointCoordinates(),
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
        features.ReCurvature(),
    ]
    for algorithm in algorithms:
        recording = testhelper.get_symbol_as_handwriting(292934)
        algorithm(recording)


def test_stroke_intersection1():
    """A '&' has one stroke. This stroke intersects itself once."""
    recording = testhelper.get_symbol_as_handwriting(97705)
    feature = features.StrokeIntersections(1)
    assert feature(recording) == [2]


def test_stroke_intersection2():
    """A 't' has two strokes. They don't intersect themselves, but they
       intersect once."""
    recording = testhelper.get_symbol_as_handwriting(293035)
    feature = features.StrokeIntersections(2)
    assert feature(recording) == [0, 1, 0]


def test_recurvature():
    """A 'o' ends in itself. The re-curvature is therefore 0."""
    recording = testhelper.get_symbol_as_handwriting(293036)
    feature = features.ReCurvature(1)
    feature(recording)
