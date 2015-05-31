#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Feature extraction algorithms.

Each algorithm works on the HandwrittenData class. They have to be applied like
this:

 >>> import features
 >>> a = HandwrittenData(...)
 >>> feature_list = [features.StrokeCount(),
                     features.ConstantPointCoordinates(strokes=4,
                                                       points_per_stroke=20,
                                                       fill_empty_with=0)
                    ]
 >>> x = a.feature_extraction(feature_list)
"""

import logging
import sys
from itertools import combinations_with_replacement as combinations_wr
import numpy
import abc

# hwrt modules
from . import HandwrittenData
from . import preprocessing
from . import utils
from . import geometry


def get_features(model_description_features):
    """Get features from a list of dictionaries

    Parameters
    ----------
    model_description_features : list of dictionaries

    Examples
    --------
    >>> l = [{'StrokeCount': None}, \
             {'ConstantPointCoordinates': \
              [{'strokes': 4}, \
               {'points_per_stroke': 81}, \
               {'fill_empty_with': 0}, \
               {'pen_down': False}] \
             } \
            ]
    >>> get_features(l)
    [StrokeCount, ConstantPointCoordinates
     - strokes: 4
     - points per stroke: 81
     - fill empty with: 0
     - pen down feature: False
    ]
    """
    return utils.get_objectlist(model_description_features,
                                config_key='features',
                                module=sys.modules[__name__])


def print_featurelist(feature_list):
    """
    Print the feature_list in a human-readable form.

    Parameters
    ----------
    feature_list : list
        feature objects
    """
    input_features = sum(map(lambda n: n.get_dimension(), feature_list))
    print("## Features (%i)" % input_features)
    print("```")
    for algorithm in feature_list:
        print("* %s" % str(algorithm))
    print("```")


class Feature(object):

    """Abstract class which defines which methods to implement for features."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __call__(self, handwritten_data):
        """Get the features value for a given recording ``handwritten_data``.
        """
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)

    @abc.abstractmethod
    def get_dimension(self):
        """Return the length of the list which __call__ will return."""


# Only feature calculation classes follow

# Every feature class must have a __str__, __repr__ function so that error
# messages can help you to find and fix bugs in features.
# Every feature class must have a __call__ function which is used to get the
# features value(s) for a given recording.
# Every feature class must have a get_dimension function so that the total
# number of features can be calculated and checked for consistency.
#
# * __call__ must take exactly one argument of type HandwrittenData
# * __call__ must return a list of length get_dimension()
# * get_dimension must return a positive number
# * have a 'normalize' attribute that is either True or False


# Local features


class ConstantPointCoordinates(Feature):

    """Take the first ``points_per_stroke=20`` points coordinates of the first
       ``strokes=4`` strokes as features. This leads to
       :math:`2 \\cdot \\text{points_per_stroke} \\cdot \\text{strokes}`
       features.

       If ``points`` is set to 0, the first ``points_per_stroke`` point
       coordinates and the ``pen_down`` feature is used. This leads to
       :math:`3 \\cdot \\text{points_per_stroke}` features."""

    normalize = False

    def __init__(self, strokes=4, points_per_stroke=20, fill_empty_with=0,
                 pen_down=True):
        self.strokes = strokes
        self.points_per_stroke = points_per_stroke
        self.fill_empty_with = fill_empty_with
        self.pen_down = pen_down

    def __repr__(self):
        return ("ConstantPointCoordinates\n"
                " - strokes: %i\n"
                " - points per stroke: %i\n"
                " - fill empty with: %i\n"
                " - pen down feature: %r\n") % \
               (self.strokes, self.points_per_stroke, self.fill_empty_with,
                self.pen_down)

    def __str__(self):
        return ("constant point coordinates\n"
                " - strokes: %i\n"
                " - points per stroke: %i\n"
                " - fill empty with: %i\n"
                " - pen down feature: %r\n") % \
               (self.strokes, self.points_per_stroke, self.fill_empty_with,
                self.pen_down)

    def get_dimension(self):
        """Get the dimension of the returned feature. This equals the number
           of elements in the returned list of numbers."""
        if self.strokes > 0:
            return 2*self.strokes * self.points_per_stroke
        else:
            if self.pen_down:
                return 3*self.points_per_stroke
            else:
                return 2*self.points_per_stroke

    def _features_with_strokes(self, handwritten_data):
        """Calculate the ConstantPointCoordinates features for the case of
           a fixed number of strokes."""
        x = []
        pointlist = handwritten_data.get_pointlist()
        for stroke_nr in range(self.strokes):
            # make sure that the current symbol actually has that many
            # strokes
            if stroke_nr < len(pointlist):
                for point_nr in range(self.points_per_stroke):
                    if point_nr < len(pointlist[stroke_nr]):
                        x.append(pointlist[stroke_nr][point_nr]['x'])
                        x.append(pointlist[stroke_nr][point_nr]['y'])
                    else:
                        x.append(self.fill_empty_with)
                        x.append(self.fill_empty_with)
            else:
                for _ in range(self.points_per_stroke):
                    x.append(self.fill_empty_with)
                    x.append(self.fill_empty_with)
        return x

    def _features_without_strokes(self, handwritten_data):
        """Calculate the ConstantPointCoordinates features for the case of
           a single (callapesed) stroke with pen_down features."""
        x = []
        for point in handwritten_data.get_pointlist()[0]:
            if len(x) >= 3*self.points_per_stroke or \
               (len(x) >= 2*self.points_per_stroke and not self.pen_down):
                break
            x.append(point['x'])
            x.append(point['y'])
            if self.pen_down:
                if 'pen_down' not in point:
                    logging.error("The "
                                  "ConstantPointCoordinates(strokes=0) "
                                  "feature should only be used after "
                                  "SpaceEvenly preprocessing step.")
                else:
                    x.append(int(point['pen_down']))
        if self.pen_down:
            while len(x) != 3*self.points_per_stroke:
                x.append(self.fill_empty_with)
        else:
            while len(x) != 2*self.points_per_stroke:
                x.append(self.fill_empty_with)
        return x

    def __call__(self, handwritten_data):
        super(self.__class__, self).__call__(handwritten_data)
        if self.strokes > 0:
            x = self._features_with_strokes(handwritten_data)
        else:
            x = self._features_without_strokes(handwritten_data)
        assert self.get_dimension() == len(x), \
            "Dimension of %s should be %i, but was %i" % \
            (str(self), self.get_dimension(), len(x))
        return x


class FirstNPoints(Feature):

    """Similar to the ``ConstantPointCoordinates`` feature, this feature takes
       the first ``n=81`` point coordinates. It also has the
       ``fill_empty_with=0`` to make sure that the dimension of this feature is
       always the same."""

    normalize = False

    def __init__(self, n=81):
        self.n = n

    def __repr__(self):
        return ("FirstNPoints\n"
                " - n: %i\n") % \
               (self.n)

    def __str__(self):
        return ("first n points\n"
                " - n: %i\n") % \
               (self.n)

    def get_dimension(self):
        """Get the dimension of the returned feature. This equals the number
           of elements in the returned list of numbers."""
        return 2*self.n

    def __call__(self, handwritten_data):
        super(self.__class__, self).__call__(handwritten_data)
        x = []
        pointlist = handwritten_data.get_pointlist()
        left = self.n
        for stroke in pointlist:
            for point in stroke:
                if left == 0:
                    break
                else:
                    left -= 1
                    x.append(point['x'])
                    x.append(point['y'])
        assert self.get_dimension() == len(x), \
            "Dimension of %s should be %i, but was %i" % \
            (str(self), self.get_dimension(), len(x))
        return x


# Global features

class StrokeCount(Feature):

    """Stroke count as a 1 dimensional recording."""

    normalize = True

    def __repr__(self):
        return "StrokeCount"

    def __str__(self):
        return "stroke count"

    def get_dimension(self):  # pylint: disable=R0201
        """Get the dimension of the returned feature. This equals the number
           of elements in the returned list of numbers."""
        return 1

    def __call__(self, handwritten_data):
        super(self.__class__, self).__call__(handwritten_data)
        return [len(handwritten_data.get_pointlist())]


class Ink(Feature):

    """Ink as a 1 dimensional feature. It gives a numeric value for the amount
       of ink this would eventually have consumed.
    """

    normalize = True

    def __repr__(self):
        return "Ink"

    def __str__(self):
        return "ink"

    def get_dimension(self):  # pylint: disable=R0201
        """Get the dimension of the returned feature. This equals the number
           of elements in the returned list of numbers."""
        return 1

    def __call__(self, handwritten_data):
        super(self.__class__, self).__call__(handwritten_data)
        ink = 0.
        # calculate ink used for this symbol
        # TODO: What about dots? What about speed?
        for stroke in handwritten_data.get_pointlist():
            last_point = None
            for point in stroke:
                if last_point is not None:
                    ink += preprocessing.euclidean_distance(last_point, point)
                last_point = point
        return [ink]


class AspectRatio(Feature):

    """Aspect ratio of a recording as a 1 dimensional feature."""

    normalize = True

    def __repr__(self):
        return "Aspect Ratio"

    def __str__(self):
        return "Aspect Ratio"

    def get_dimension(self):  # pylint: disable=R0201
        """Get the dimension of the returned feature. This equals the number
           of elements in the returned list of numbers."""
        return 1

    def __call__(self, handwritten_data):
        super(self.__class__, self).__call__(handwritten_data)
        width = float(handwritten_data.get_width()+0.01)
        height = float(handwritten_data.get_height()+0.01)
        return [width/height]


class Width(Feature):

    """Width of a recording as a 1 dimensional feature.

    .. note::

        This is the current width. So if the recording was scaled, this will
        not be the original width.
    """

    normalize = True

    def __repr__(self):
        return "Width"

    def __str__(self):
        return "Width"

    def get_dimension(self):  # pylint: disable=R0201
        """Get the dimension of the returned feature. This equals the number
           of elements in the returned list of numbers."""
        return 1

    def __call__(self, handwritten_data):
        super(self.__class__, self).__call__(handwritten_data)
        return [float(handwritten_data.get_width())]


class Height(Feature):

    """Height of a recording as a a 1 dimensional feature.

    .. note::

        This is the current hight. So if the recording was scaled, this will
        not be the original height.
    """

    normalize = True

    def __repr__(self):
        return "Height"

    def __str__(self):
        return "Height"

    def get_dimension(self):  # pylint: disable=R0201
        """Get the dimension of the returned feature. This equals the number
           of elements in the returned list of numbers."""
        return 1

    def __call__(self, handwritten_data):
        super(self.__class__, self).__call__(handwritten_data)
        return [float(handwritten_data.get_height())]


class Time(Feature):

    """The time in milliseconds it took to create the recording. This is a 1
       dimensional feature."""

    normalize = True

    def __repr__(self):
        return "Time"

    def __str__(self):
        return "Time"

    def get_dimension(self):  # pylint: disable=R0201
        """Get the dimension of the returned feature. This equals the number
           of elements in the returned list of numbers."""
        return 1

    def __call__(self, handwritten_data):
        super(self.__class__, self).__call__(handwritten_data)
        return [float(handwritten_data.get_time())]


class CenterOfMass(Feature):

    """Center of mass of a recording as a 2 dimensional feature."""

    normalize = True

    def __repr__(self):
        return "CenterOfMass"

    def __str__(self):
        return "Center of mass"

    def get_dimension(self):  # pylint: disable=R0201
        """Get the dimension of the returned feature. This equals the number
           of elements in the returned list of numbers."""
        return 2

    def __call__(self, handwritten_data):
        super(self.__class__, self).__call__(handwritten_data)
        xs = []
        ys = []
        for stroke in handwritten_data.get_pointlist():
            for point in stroke:
                xs.append(point['x'])
                ys.append(point['y'])
        return [float(sum(xs))/len(xs), float(sum(ys))/len(ys)]


class StrokeCenter(Feature):

    """Get the stroke center of mass coordinates as a 2 dimensional feature."""

    normalize = True

    def __init__(self, strokes=4):
        self.strokes = strokes

    def __repr__(self):
        return "StrokeCenter"

    def __str__(self):
        return "Stroke center"

    def get_dimension(self):
        """Get the dimension of the returned feature. This equals the number
           of elements in the returned list of numbers."""
        return self.strokes*2

    def __call__(self, handwritten_data):
        super(self.__class__, self).__call__(handwritten_data)
        feature_vector = []
        for i, stroke in enumerate(handwritten_data.get_pointlist()):
            if i >= self.strokes:
                break
            xs = []
            ys = []
            for point in stroke:
                xs.append(point['x'])
                ys.append(point['y'])
            feature_vector.append(numpy.mean(xs))
            feature_vector.append(numpy.mean(ys))
        while len(feature_vector) < self.get_dimension():
            feature_vector.append(0)
        return feature_vector


class StrokeIntersections(Feature):
    """Count the number of intersections which strokes in the recording have
       with each other in form of a symmetrical matrix for the first
       ``stroke=4`` strokes. The feature dimension is
       :math:`round(\\frac{\\text{strokes}^2}{2} + \\frac{\\text{strokes}}{2})`
       because the symmetrical part is discarded.

    =======   ======= ======= ======= ===
      -       stroke1 stroke2 stroke3
    -------   ------- ------- ------- ---
    stroke1     0        1      0     ...
    stroke2     1        2      0     ...
    stroke3     0        0      0     ...
    ...         ...      ...    ...   ...
    =======   ======= ======= ======= ===

    Returns values of upper triangular matrix (including diagonal)
    from left to right, top to bottom.

    ..warning

        This method has an error. It should probably not be used.
    """

    normalize = True

    def __init__(self, strokes=4):
        self.strokes = strokes

    def __repr__(self):
        return "StrokeIntersections"

    def __str__(self):
        return "StrokeIntersections"

    def get_dimension(self):
        """Get the dimension of the returned feature. This equals the number
           of elements in the returned list of numbers."""
        return int(round(float(self.strokes**2)/2 + float(self.strokes)/2))

    def __call__(self, handwritten_data):
        super(self.__class__, self).__call__(handwritten_data)

        pointlist = handwritten_data.get_pointlist()
        polygonalChains = []

        # Make sure the dimension is correct
        for i in range(self.strokes):
            if i < len(pointlist):
                polygonalChains.append(geometry.PolygonalChain(pointlist[i]))
            else:
                polygonalChains.append(geometry.PolygonalChain([]))

        x = []
        for chainA, chainB in combinations_wr(polygonalChains, 2):
            if chainA == chainB:
                x.append(chainA.count_selfintersections())
            else:
                x.append(chainA.count_intersections(chainB))

        assert self.get_dimension() == len(x), \
            "Dimension of %s should be %i, but was %i" % \
            (str(self), self.get_dimension(), len(x))
        return x


class ReCurvature(Feature):

    """Re-curvature is a 1 dimensional, stroke-global feature for a recording.
       It is the ratio
       :math:`\\frac{\\text{height}(s)}{\\text{length}(s)}`.
       If ``length(s) == 0``, then the re-curvature is defined to be 1.
    """

    normalize = True

    def __init__(self, strokes=4):
        assert strokes > 0, \
            "This attribute has to be positive, but was %s" % \
            str(strokes)
        self.strokes = strokes

    def __repr__(self):
        return "ReCurvature"

    def __str__(self):
        return "Re-curvature"

    def get_dimension(self):
        """Get the dimension of the returned feature. This equals the number
           of elements in the returned list of numbers."""
        return self.strokes

    def __call__(self, handwritten_data):
        super(self.__class__, self).__call__(handwritten_data)
        x = []
        for stroke in handwritten_data.get_pointlist():
            stroke_y = [point['y'] for point in stroke]
            height = max(stroke_y) - min(stroke_y)
            length = 0.0
            for last_point, point in zip(stroke, stroke[1:]):
                length += preprocessing.euclidean_distance(point, last_point)

            if length == 0:
                x.append(1)
            else:
                x.append(height/length)
            if len(x) == self.strokes:
                break
        while len(x) < self.strokes:
            x.append(0)
        assert self.get_dimension() == len(x), \
            "Dimension of %s should be %i, but was %i" % \
            (str(self), self.get_dimension(), len(x))
        return x


if __name__ == '__main__':
    import doctest
    doctest.testmod()
