#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third party modules
import nose

# First party modules
import hwrt.data_multiplication as data_multiplication
import tests.testhelper as testhelper


# Tests
def data_multiplication_detection_test():
    l = [
        {"Multiply": None},
        {"Multiply": [{"nr": 1}]},
        {"Rotate": [{"minimum": -3}, {"maximum": +3}, {"num": 3}]},
    ]
    correct = [
        data_multiplication.Multiply(nr=1),
        data_multiplication.Multiply(nr=1),
        data_multiplication.Rotate(minimum=-3, maximum=3, num=3),
    ]
    mult_queue = data_multiplication.get_data_multiplication_queue(l)
    # TODO: Not only compare lengths of lists but actual contents.
    nose.tools.assert_equal(len(mult_queue), len(correct))


def rotate_test():
    recording = testhelper.get_symbol_as_handwriting(292934)
    rotation = data_multiplication.Rotate(minimum=-3, maximum=3, num=3)
    new_recordings = rotation(recording)
    # TODO: Not only compare lengths of lists but actual contents.
    nose.tools.assert_equal(len(new_recordings), 3)
