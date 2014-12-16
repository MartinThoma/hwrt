#!/usr/bin/env python
# -*- coding: utf-8 -*-

import nose
import tests.testhelper as testhelper

# hwrt modules
from hwrt.HandwrittenData import HandwrittenData
import hwrt.preprocessing as preprocessing


# Tests
def preprocessing_detection_test():
    preprocessing_queue = [{'ScaleAndShift': None},
                           {'StrokeConnect': None},
                           {'DouglasPeucker': [{'epsilon': 0.2}]},
                           {'SpaceEvenly': [{'number': 100}]}]
    correct = [preprocessing.ScaleAndShift(),
               preprocessing.StrokeConnect(),
               preprocessing.DouglasPeucker(epsilon=0.2),
               preprocessing.SpaceEvenly(number=100)]
    feature_list = preprocessing.get_preprocessing_queue(preprocessing_queue)
    # TODO: Not only compare lengths of lists but actual contents.
    nose.tools.assert_equal(len(feature_list), len(correct))


def simple_execution_test():
    algorithms = [preprocessing.RemoveDuplicateTime(),
                  preprocessing.RemoveDots(),
                  preprocessing.SpaceEvenly(),
                  preprocessing.SpaceEvenlyPerStroke(),
                  preprocessing.DouglasPeucker(),
                  preprocessing.StrokeConnect(),
                  preprocessing.DotReduction(),
                  preprocessing.WildPointFilter(),
                  preprocessing.WeightedAverageSmoothing()]
    for algorithm in algorithms:
        a = testhelper.get_symbol_as_handwriting(292934)
        algorithm(a)


def euclidean_distance_test():
    p1 = {'x': 12, 'y': 15}
    p2 = {'x':  2, 'y': 50}
    dist = preprocessing.euclidean_distance(p1, p2)
    nose.tools.assert_equal(round(dist, 1), 36.4)


def ScaleAndShift_test_all():
    preprocessing_queue = [preprocessing.ScaleAndShift()]
    for a in testhelper.get_all_symbols_as_handwriting():
        a.preprocessing(preprocessing_queue)
        s = a.get_pointlist()
        assert len(s) > 0


def ScaleAndShift_test_simple_1():
    preprocessing_queue = [preprocessing.ScaleAndShift()]
    s = '[[{"x":0, "y":0, "time": 0}]]'
    a = HandwrittenData(s)
    a.preprocessing(preprocessing_queue)
    s = a.get_pointlist()
    expectation = [[{"x": 0, "y": 0, "time": 0}]]
    assert s == expectation, "Got: %s; expected %s" % (s, expectation)


def ScaleAndShift_test_simple_2():
    preprocessing_queue = [preprocessing.ScaleAndShift()]
    s = '[[{"x":10, "y":0, "time": 0}]]'
    a = HandwrittenData(s)
    a.preprocessing(preprocessing_queue)
    s = a.get_pointlist()
    expectation = [[{"x": 0, "y": 0, "time": 0}]]
    assert s == expectation, "Got: %s; expected %s" % (s, expectation)


def ScaleAndShift_test_simple_3():
    preprocessing_queue = [preprocessing.ScaleAndShift()]
    s = '[[{"x":0, "y":10, "time": 0}]]'
    a = HandwrittenData(s)
    a.preprocessing(preprocessing_queue)
    s = a.get_pointlist()
    expectation = [[{"x": 0, "y": 0, "time": 0}]]
    assert s == expectation, "Got: %s; expected %s" % (s, expectation)


def ScaleAndShift_test_simple_4():
    preprocessing_queue = [preprocessing.ScaleAndShift()]
    s = '[[{"x":0, "y":0, "time": 10}]]'
    a = HandwrittenData(s)
    a.preprocessing(preprocessing_queue)
    s = a.get_pointlist()
    expectation = [[{"x": 0, "y": 0, "time": 0}]]
    assert s == expectation, "Got: %s; expected %s" % (s, expectation)


def ScaleAndShift_test_simple_5():
    preprocessing_queue = [preprocessing.ScaleAndShift()]
    s = '[[{"x":42, "y":12, "time": 10}]]'
    a = HandwrittenData(s)
    a.preprocessing(preprocessing_queue)
    s = a.get_pointlist()
    expectation = [[{"x": 0, "y": 0, "time": 0}]]
    assert s == expectation, "Got: %s; expected %s" % (s, expectation)


def ScaleAndShift_test_a():
    preprocessing_queue = [preprocessing.ScaleAndShift()]
    s = ('[[{"x":232,"y":423,"time":1407885913983},'
         '{"x":267,"y":262,"time":1407885914315},'
         '{"x":325,"y":416,"time":1407885914650}],'
         '[{"x":252,"y":355,"time":1407885915675},'
         '{"x":305,"y":351,"time":1407885916361}]]')
    a = HandwrittenData(s)
    a.preprocessing(preprocessing_queue)
    s = a.get_pointlist()
    expectation = [[{u'y': 1.0, u'x': 0.0, u'time': 0},
                    {u'y': 0.0, u'x': 0.2174, u'time': 332},
                    {u'y': 0.9565, u'x': 0.5776, u'time': 667}],
                   [{u'y': 0.5776, u'x': 0.1242, u'time': 1692},
                    {u'y': 0.5528, u'x': 0.4534, u'time': 2378}]]
    assert testhelper.compare_pointlists(s, expectation), \
        "Got: %s; expected %s" % (s, expectation)


def ScaleAndShift_test_a_center():
    preprocessing_queue = [preprocessing.ScaleAndShift(center=True)]
    s = ('[[{"y": 1.0, "x": -0.3655913978494625, "time": 0}, '
         '{"y": 0.0, "x": -0.1482000935016364, "time": 332}, '
         '{"y": 0.9565, "x": 0.21204835370333253, "time": 667}], '
         '[{"y": 0.5776, "x": -0.24136779536499045, "time": 1692}, '
         '{"y": 0.5528, "x": 0.08782475121886046, "time": 2378}]]')
    a = HandwrittenData(s)
    a.preprocessing(preprocessing_queue)
    s = a.get_pointlist()
    expectation = [[{u'y': 1.0, u'x': -0.2888198757763975, u'time': 0},
                    {u'y': 0.0, u'x': -0.07142857142857142, u'time': 332},
                    {u'y': 0.9565, u'x': 0.2888198757763975, u'time': 667}],
                   [{u'y': 0.5776, u'x': -0.16459627329192547, u'time': 1692},
                    {u'y': 0.5528, u'x': 0.16459627329192544, u'time': 2378}]]
    assert testhelper.compare_pointlists(s, expectation), \
        "Got: %s; expected %s" % (s, expectation)


def space_evenly_per_stroke_test_all():
    preprocessing_queue = [preprocessing.SpaceEvenlyPerStroke(number=100,
                                                              kind='cubic')]
    for a in testhelper.get_all_symbols_as_handwriting():
        a.preprocessing(preprocessing_queue)
        s = a.get_pointlist()
        print(s)
        assert len(s) > 0
