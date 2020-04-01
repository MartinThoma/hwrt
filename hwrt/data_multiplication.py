#!/usr/bin/env python

"""Data multiplication algorithms.

Each algorithm works on the HandwrittenData class. They have to be applied like
this:

>>> from hwrt.handwritten_data import HandwrittenData
>>> data_json = '[[{"time": 123, "x": 45, "y": 67}]]'
>>> a = HandwrittenData(raw_data_id=2953, raw_data_json=data_json)
>>> multiplication_queue = [Multiply(10),
...                         Rotate(-30, 30, 5)]
>>> x = [f(a) for f in multiplication_queue]

"""

# Core Library modules
import math
import sys
from copy import deepcopy

# Third party modules
import numpy

# Local modules
from . import handwritten_data, utils


def get_data_multiplication_queue(model_description_multiply):
    """Get features from a list of dictionaries

    >>> l = [{'Multiply': [{'nr': 1}]}, \
             {'Rotate': [{'minimum':-30}, {'maximum': 30}, {'num': 5}]}]
    >>> get_data_multiplication_queue(l)
    [Multiply (1 times), Rotate (-30.00, 30.00, 5.00)]
    """
    return utils.get_objectlist(
        model_description_multiply,
        config_key="data_multiplication",
        module=sys.modules[__name__],
    )


# Only data multiplication classes follow
# Everyone must have a __str__, __repr__, __call__ and get_dimension function
# where
# * __call__ must take exactly one argument of type HandwrittenData
# * __call__ must return a list of HandwrittenData objects


# Local features


class Multiply:

    """Copy the data n times."""

    def __init__(self, nr=1):
        self.nr = nr

    def __repr__(self):
        return "Multiply (%i times)" % self.nr

    def __str__(self):
        return repr(self)

    def __call__(self, hwr_obj):
        assert isinstance(
            hwr_obj, handwritten_data.HandwrittenData
        ), "handwritten data is not of type HandwrittenData, but of %r" % type(hwr_obj)
        new_trainging_set = []
        for _ in range(self.nr):
            new_trainging_set.append(hwr_obj)
        training_set = new_trainging_set
        return training_set


class Rotate:

    """Add rotational variants of the recording."""

    def __init__(self, minimum=-30.0, maximum=30.0, num=5):
        self.min = minimum
        self.max = maximum
        self.num = num

    def __repr__(self):
        return f"Rotate ({self.min:0.2f}, {self.max:0.2f}, {self.num:0.2f})"

    def __str__(self):
        return repr(self)

    def __call__(self, hwr_obj):
        assert isinstance(
            hwr_obj, handwritten_data.HandwrittenData
        ), "handwritten data is not of type HandwrittenData, but of %r" % type(hwr_obj)
        new_trainging_set = []
        xc, yc = hwr_obj.get_center_of_mass()
        pointlist = hwr_obj.get_pointlist()
        for rotation in numpy.linspace(self.min, self.max, self.num):
            new_poinlist = []
            # Rotate pointlist around center of mass (xc, yc)
            for line in pointlist:
                new_line = []
                for point in line:
                    # Calculate rotation
                    # xnew, ynew = xc, yc
                    # (xnew, ynew) += (x-xc, y-yc)* (cos(rot.)  -sin(rot.))
                    #                               (sin(rot.)   cos(rot.))
                    x, y = point["x"], point["y"]
                    cos = math.cos(math.radians(rotation))
                    sin = math.sin(math.radians(rotation))
                    xnew = cos * (x - xc) - sin * (y - yc) + xc
                    ynew = sin * (x - xc) + cos * (y - yc) + yc
                    new_line.append({"x": xnew, "y": ynew, "time": point["time"]})
                new_poinlist.append(new_line)
            # create the new handwritten data object
            hwd_tmp = deepcopy(hwr_obj)
            hwd_tmp.set_pointlist(new_poinlist)
            new_trainging_set.append(hwd_tmp)
        training_set = new_trainging_set
        return training_set
