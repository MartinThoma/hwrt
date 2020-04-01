#!/usr/bin/env python

# First party modules
import hwrt.data_multiplication as data_multiplication
import tests.testhelper as testhelper


def test_data_multiplication_detection():
    queue = [
        {"Multiply": None},
        {"Multiply": [{"nr": 1}]},
        {"Rotate": [{"minimum": -3}, {"maximum": +3}, {"num": 3}]},
    ]
    correct = [
        data_multiplication.Multiply(nr=1),
        data_multiplication.Multiply(nr=1),
        data_multiplication.Rotate(minimum=-3, maximum=3, num=3),
    ]
    mult_queue = data_multiplication.get_data_multiplication_queue(queue)
    # TODO: Not only compare lengths of lists but actual contents.
    assert len(mult_queue) == len(correct)


def test_rotate():
    recording = testhelper.get_symbol_as_handwriting(292934)
    rotation = data_multiplication.Rotate(minimum=-3, maximum=3, num=3)
    new_recordings = rotation(recording)
    # TODO: Not only compare lengths of lists but actual contents.
    assert len(new_recordings) == 3
