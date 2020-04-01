#!/usr/bin/env python

# First party modules
import hwrt.preprocessing as preprocessing
import tests.testhelper as testhelper
from hwrt.handwritten_data import HandwrittenData


# Tests
def test_preprocessing_detection_test():
    preprocessing_queue = [
        {"ScaleAndShift": None},
        {"StrokeConnect": None},
        {"DouglasPeucker": [{"epsilon": 0.2}]},
        {"SpaceEvenly": [{"number": 100}]},
    ]
    correct = [
        preprocessing.ScaleAndShift(),
        preprocessing.StrokeConnect(),
        preprocessing.DouglasPeucker(epsilon=0.2),
        preprocessing.SpaceEvenly(number=100),
    ]
    feature_list = preprocessing.get_preprocessing_queue(preprocessing_queue)
    # TODO: Not only compare lengths of lists but actual contents.
    assert len(feature_list) == len(correct)


def test_simple_execution_test():
    algorithms = [
        preprocessing.RemoveDuplicateTime(),
        preprocessing.RemoveDots(),
        preprocessing.SpaceEvenly(),
        preprocessing.SpaceEvenlyPerStroke(),
        preprocessing.DouglasPeucker(),
        preprocessing.StrokeConnect(),
        preprocessing.DotReduction(),
        preprocessing.WildPointFilter(),
        preprocessing.WeightedAverageSmoothing(),
    ]
    for algorithm in algorithms:
        a = testhelper.get_symbol_as_handwriting(292934)
        algorithm(a)


def test_euclidean_distance_test():
    p1 = {"x": 12, "y": 15}
    p2 = {"x": 2, "y": 50}
    dist = preprocessing.euclidean_distance(p1, p2)
    assert round(dist, 1) == 36.4


def test_ScaleAndShift_test_all():
    preprocessing_queue = [preprocessing.ScaleAndShift()]
    for a in testhelper.get_all_symbols_as_handwriting():
        a.preprocessing(preprocessing_queue)
        s = a.get_pointlist()
        assert len(s) > 0


def test_ScaleAndShift_test_simple_1():
    preprocessing_queue = [preprocessing.ScaleAndShift()]
    s = '[[{"x":0, "y":0, "time": 0}]]'
    a = HandwrittenData(s)
    a.preprocessing(preprocessing_queue)
    s = a.get_pointlist()
    expectation = [[{"x": 0, "y": 0, "time": 0}]]
    assert s == expectation, f"Got: {s}; expected {expectation}"


def test_ScaleAndShift_test_simple_2():
    preprocessing_queue = [preprocessing.ScaleAndShift()]
    s = '[[{"x":10, "y":0, "time": 0}]]'
    a = HandwrittenData(s)
    a.preprocessing(preprocessing_queue)
    s = a.get_pointlist()
    expectation = [[{"x": 0, "y": 0, "time": 0}]]
    assert s == expectation, f"Got: {s}; expected {expectation}"


def test_ScaleAndShift_test_simple_3():
    preprocessing_queue = [preprocessing.ScaleAndShift()]
    s = '[[{"x":0, "y":10, "time": 0}]]'
    a = HandwrittenData(s)
    a.preprocessing(preprocessing_queue)
    s = a.get_pointlist()
    expectation = [[{"x": 0, "y": 0, "time": 0}]]
    assert s == expectation, f"Got: {s}; expected {expectation}"


def test_ScaleAndShift_test_simple_4():
    preprocessing_queue = [preprocessing.ScaleAndShift()]
    s = '[[{"x":0, "y":0, "time": 10}]]'
    a = HandwrittenData(s)
    a.preprocessing(preprocessing_queue)
    s = a.get_pointlist()
    expectation = [[{"x": 0, "y": 0, "time": 0}]]
    assert s == expectation, f"Got: {s}; expected {expectation}"


def test_ScaleAndShift_test_simple_5():
    preprocessing_queue = [preprocessing.ScaleAndShift()]
    s = '[[{"x":42, "y":12, "time": 10}]]'
    a = HandwrittenData(s)
    a.preprocessing(preprocessing_queue)
    s = a.get_pointlist()
    expectation = [[{"x": 0, "y": 0, "time": 0}]]
    assert s == expectation, f"Got: {s}; expected {expectation}"


def test_ScaleAndShift_test_a():
    preprocessing_queue = [preprocessing.ScaleAndShift()]
    s = (
        '[[{"x":232,"y":423,"time":1407885913983},'
        '{"x":267,"y":262,"time":1407885914315},'
        '{"x":325,"y":416,"time":1407885914650}],'
        '[{"x":252,"y":355,"time":1407885915675},'
        '{"x":305,"y":351,"time":1407885916361}]]'
    )
    a = HandwrittenData(s)
    a.preprocessing(preprocessing_queue)
    s = a.get_pointlist()
    expectation = [
        [
            {"y": 1.0, "x": 0.0, "time": 0},
            {"y": 0.0, "x": 0.2174, "time": 332},
            {"y": 0.9565, "x": 0.5776, "time": 667},
        ],
        [
            {"y": 0.5776, "x": 0.1242, "time": 1692},
            {"y": 0.5528, "x": 0.4534, "time": 2378},
        ],
    ]
    assert testhelper.compare_pointlists(
        s, expectation
    ), f"Got: {s}; expected {expectation}"


def test_ScaleAndShift_test_a_center():
    preprocessing_queue = [preprocessing.ScaleAndShift(center=True)]
    s = (
        '[[{"y": 1.0, "x": -0.3655913978494625, "time": 0}, '
        '{"y": 0.0, "x": -0.1482000935016364, "time": 332}, '
        '{"y": 0.9565, "x": 0.21204835370333253, "time": 667}], '
        '[{"y": 0.5776, "x": -0.24136779536499045, "time": 1692}, '
        '{"y": 0.5528, "x": 0.08782475121886046, "time": 2378}]]'
    )
    a = HandwrittenData(s)
    a.preprocessing(preprocessing_queue)
    s = a.get_pointlist()
    expectation = [
        [
            {"y": 1.0, "x": -0.2888198757763975, "time": 0},
            {"y": 0.0, "x": -0.07142857142857142, "time": 332},
            {"y": 0.9565, "x": 0.2888198757763975, "time": 667},
        ],
        [
            {"y": 0.5776, "x": -0.16459627329192547, "time": 1692},
            {"y": 0.5528, "x": 0.16459627329192544, "time": 2378},
        ],
    ]
    assert testhelper.compare_pointlists(
        s, expectation
    ), f"Got: {s}; expected {expectation}"


def test_space_evenly_per_stroke_test_all():
    preprocessing_queue = [preprocessing.SpaceEvenlyPerStroke(number=100, kind="cubic")]
    for a in testhelper.get_all_symbols_as_handwriting():
        a.preprocessing(preprocessing_queue)
        s = a.get_pointlist()
        print(s)
        assert len(s) > 0
