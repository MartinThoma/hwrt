#!/usr/bin/env python
# -*- coding: utf-8 -*-

import nose.tools
import tests.testhelper as testhelper
import mock

# hwrt modules
from hwrt.HandwrittenData import HandwrittenData


# Tests
def load_symbol_test():
    for symbol_file in testhelper.get_all_symbols():
        with open(symbol_file) as f:
            data = f.read()
        a = HandwrittenData(data)
        assert isinstance(a, HandwrittenData)


def set_pointlist_test():
    a = testhelper.get_symbol_as_handwriting(97705)
    a.set_pointlist([[]])
    nose.tools.assert_equal(a.get_pointlist(), [[]])


def get_sorted_pointlist_test():
    a = testhelper.get_symbol_as_handwriting(97705)
    nose.tools.assert_equal(a.get_sorted_pointlist(),
                            [[
                             {'y': 223.125, 'x': 328.5, 'time': 1377173554837},
                             {'y': 225.125, 'x': 326.5, 'time': 1377173554868},
                             {'y': 226.125, 'x': 322.5, 'time': 1377173554876},
                             {'y': 229.125, 'x': 319.5, 'time': 1377173554885},
                             {'y': 231.125, 'x': 315.5, 'time': 1377173554895},
                             {'y': 237.125, 'x': 304.5, 'time': 1377173554912},
                             {'y': 245.125, 'x': 291.5, 'time': 1377173554928},
                             {'y': 253.125, 'x': 274.5, 'time': 1377173554945},
                             {'y': 261.125, 'x': 256.5, 'time': 1377173554964},
                             {'y': 267.125, 'x': 243.5, 'time': 1377173554978},
                             {'y': 276.125, 'x': 222.5, 'time': 1377173554995},
                             {'y': 279.125, 'x': 211.5, 'time': 1377173555012},
                             {'y': 280.125, 'x': 204.5, 'time': 1377173555031},
                             {'y': 281.125, 'x': 196.5, 'time': 1377173555045},
                             {'y': 281.125, 'x': 183.5, 'time': 1377173555061},
                             {'y': 281.125, 'x': 172.5, 'time': 1377173555078},
                             {'y': 280.125, 'x': 163.5, 'time': 1377173555095},
                             {'y': 274.125, 'x': 149.5, 'time': 1377173555128},
                             {'y': 270.125, 'x': 144.5, 'time': 1377173555147},
                             {'y': 266.125, 'x': 142.5, 'time': 1377173555180},
                             {'y': 258.125, 'x': 142.5, 'time': 1377173555216},
                             {'y': 226.125, 'x': 143.5, 'time': 1377173555264},
                             {'y': 212.125, 'x': 148.5, 'time': 1377173555281},
                             {'y': 204.125, 'x': 156.5, 'time': 1377173555296},
                             {'y': 182.125, 'x': 176.5, 'time': 1377173555330},
                             {'y': 167.125, 'x': 189.5, 'time': 1377173555363},
                             {'y': 152.125, 'x': 201.5, 'time': 1377173555397},
                             {'y': 148.125, 'x': 206.5, 'time': 1377173555417},
                             {'y': 132.125, 'x': 223.5, 'time': 1377173555463},
                             {'y': 121.125, 'x': 231.5, 'time': 1377173555496},
                             {'y': 106.125, 'x': 241.5, 'time': 1377173555530},
                             {'y':  94.125, 'x': 243.5, 'time': 1377173555563},
                             {'y':  81.125, 'x': 241.5, 'time': 1377173555596},
                             {'y':  75.125, 'x': 236.5, 'time': 1377173555630},
                             {'y':  62.125, 'x': 222.5, 'time': 1377173555663},
                             {'y':  54.125, 'x': 208.5, 'time': 1377173555696},
                             {'y':  50.125, 'x': 198.5, 'time': 1377173555730},
                             {'y':  50.125, 'x': 182.5, 'time': 1377173555763},
                             {'y':  50.125, 'x': 174.5, 'time': 1377173555795},
                             {'y':  57.125, 'x': 168.5, 'time': 1377173555830},
                             {'y':  67.125, 'x': 166.5, 'time': 1377173555862},
                             {'y':  80.125, 'x': 166.5, 'time': 1377173555896},
                             {'y': 102.125, 'x': 173.5, 'time': 1377173555930},
                             {'y': 130.125, 'x': 184.5, 'time': 1377173555962},
                             {'y': 157.125, 'x': 195.5, 'time': 1377173555996},
                             {'y': 176.125, 'x': 207.5, 'time': 1377173556030},
                             {'y': 194.125, 'x': 217.5, 'time': 1377173556061},
                             {'y': 207.125, 'x': 225.5, 'time': 1377173556094},
                             {'y': 215.125, 'x': 231.5, 'time': 1377173556115},
                             {'y': 229.125, 'x': 239.5, 'time': 1377173556147},
                             {'y': 242.125, 'x': 246.5, 'time': 1377173556180},
                             {'y': 259.125, 'x': 258.5, 'time': 1377173556216},
                             {'y': 274.125, 'x': 269.5, 'time': 1377173556247},
                             {'y': 282.125, 'x': 275.5, 'time': 1377173556280},
                             {'y': 290.125, 'x': 280.5, 'time': 1377173556315},
                             {'y': 292.125, 'x': 281.5, 'time': 1377173556349},
                             {'y': 292.125, 'x': 282.5, 'time': 1377173556395},
                             {'y': 293.125, 'x': 283.5, 'time': 1377173556499},
                             {'y': 295.125, 'x': 286.5, 'time': 1377173556652},
                             {'y': 300.125, 'x': 290.5, 'time': 1377173556660},
                             {'y': 304.125, 'x': 294.5, 'time': 1377173556668},
                             {'y': 307.125, 'x': 297.5, 'time': 1377173556682},
                             {'y': 311.125, 'x': 300.5, 'time': 1377173556697},
                             {'y': 313.125, 'x': 302.5, 'time': 1377173556713}]
                             ])


def count_single_dots_test():
    a = testhelper.get_symbol_as_handwriting(97705)
    a.set_pointlist([[{'x': 12, 'y': 42, 'time': 100}]])
    nose.tools.assert_equal(a.count_single_dots(), 1)


def center_of_mass_test():
    a = testhelper.get_symbol_as_handwriting(97705)
    nose.tools.assert_equal(a.get_center_of_mass(), (229.21875, 207.265625))


def equality_test():
    a = testhelper.get_symbol_as_handwriting(97705)
    nose.tools.assert_equal(a == a, True)


def inequality_test():
    a = testhelper.get_symbol_as_handwriting(97705)
    b = testhelper.get_symbol_as_handwriting(292934)
    nose.tools.assert_equal(a == b, False)
    c = []
    nose.tools.assert_equal(a == c, False)
    nose.tools.assert_equal(a != c, True)


def stringification_test():
    a = testhelper.get_symbol_as_handwriting(97705)
    nose.tools.assert_equal(str(a), "HandwrittenData(raw_data_id=None)")


def area_test():
    a = testhelper.get_symbol_as_handwriting(97705)
    # TODO: Is this really correct?
    nose.tools.assert_equal(a.get_area(), 49368.0)


def time_test():
    a = testhelper.get_symbol_as_handwriting(97705)
    nose.tools.assert_equal(a.get_time(), 1876)


def show_test():
    a = testhelper.get_symbol_as_handwriting(97705)
    with mock.patch('matplotlib.pyplot.show', return_value='yes'):
        a.show()


def width_test():
    with open(testhelper.get_symbol(97705)) as f:
        data = f.read()
    assert HandwrittenData(data).get_width() == 186, \
        "Got %i" % HandwrittenData(data).get_width()
