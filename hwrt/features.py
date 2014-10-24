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

import inspect
import urllib
import os
import Image
import logging
import sys
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)
from shapely.geometry import LineString
import itertools
import numpy
# mine
import hwrt.HandwrittenData as HandwrittenData
import hwrt.preprocessing as preprocessing


def get_class(name):
    """Get function pointer by string."""
    clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    for string_name, act_class in clsmembers:
        if string_name == name:
            return act_class
    logging.debug("Unknown feature class '%s'.", name)
    return None


def get_features(model_description_features):
    """Get features from a list of dictionaries

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
    feature_list = []
    for feature in model_description_features:
        for feat, params in feature.items():
            feat = get_class(feat)
            if params is None:
                feature_list.append(feat())
            else:
                parameters = {}
                for dicts in params:
                    for param_name, param_value in dicts.items():
                        parameters[param_name] = param_value
                feature_list.append(feat(**parameters))
    return feature_list

# Only feature calculation classes follow
# Everyone must have a __str__, __repr__, __call__ and get_dimension function
# where
# * __call__ must take exactly one argument of type HandwrittenData
# * __call__ must return a list of length get_dimension()
# * get_dimension must return a positive number
# * have a 'normalize' attribute that is either true or false


# Local features


class ConstantPointCoordinates(object):

    """Take the first `points_per_stroke=20` points coordinates of the first
       `strokes=4` strokes as features. This leads to
       :math:`2 \cdot \text{points\_per\_stroke} \cdot \text{strokes}` features.

       If `points` is set to 0, the first `points\_per\_stroke` point
       coordinates and the \verb+pen_down+ feature is used. This leads to
       :math:`3 \cdot \text{points_per_stroke}` features."""

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
        if self.strokes > 0:
            return 2*self.strokes * self.points_per_stroke
        else:
            if self.pen_down:
                return 3*self.points_per_stroke
            else:
                return 2*self.points_per_stroke

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        x = []
        pointlist = handwritten_data.get_pointlist()
        if self.strokes > 0:
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
        else:
            for point in handwritten_data.get_pointlist()[0]:
                if len(x) >= 3*self.points_per_stroke or \
                   (len(x) >= 2*self.points_per_stroke and not self.pen_down):
                    break
                x.append(point['x'])
                x.append(point['y'])
                if self.pen_down:
                    x.append(int(point['pen_down']))
            if self.pen_down:
                while len(x) != 3*self.points_per_stroke:
                    x.append(self.fill_empty_with)
            else:
                while len(x) != 2*self.points_per_stroke:
                    x.append(self.fill_empty_with)
        assert self.get_dimension() == len(x), \
            "Dimension of %s should be %i, but was %i" % \
            (self.__str__(), self.get_dimension(), len(x))
        return x


class FirstNPoints(object):

    """Similar to the `ConstantPointCoordinates` feature, this feature takes the
       first `n=81` point coordinates. It also has the `fill_empty_with=0` to
       make sure that the dimension of this feature is always the same."""

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
        return 2*self.n

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
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
            (self.__str__(), self.get_dimension(), len(x))
        return x


# Global features

class StrokeCount(object):

    """Stroke count as a 1 dimensional recording."""

    normalize = True

    def __repr__(self):
        return "StrokeCount"

    def __str__(self):
        return "stroke count"

    def get_dimension(self):
        return 1

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        return [len(handwritten_data.get_pointlist())]


class Bitmap(object):

    """n × n grayscale bitmap of the recording."""

    normalize = True

    def __init__(self, n=28):
        self.n = n  # Size of the bitmap (n x n)

    def __repr__(self):
        return ("Bitmap (n=%i)\n") % (self.n)

    def __str__(self):
        return self.__repr__()

    def get_dimension(self):
        return self.n**2

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        x = []
        url = "http://localhost/write-math/website/raw-data/"
        raw_data_id = handwritten_data.raw_data_id
        foldername = "/tmp/write-math/"
        f = urllib.urlopen("{url}{id}.svg".format(url=url, id=raw_data_id))
        with open("%s%i.svg" % (foldername, raw_data_id), "wb") as imgFile:
            imgFile.write(f.read())

        command = ("convert -size 28x28 {folder}{id}.svg  -resize {n}x{n} "
                   "-gravity center -extent {n}x{n} "
                   "-monochrome {folder}{id}.png").format(id=raw_data_id,
                                                          n=self.n,
                                                          url=url,
                                                          folder=foldername)
        os.system(command)
        im = Image.open("%s%i.png" % (foldername, raw_data_id))
        pix = im.load()
        # pixel_image = [[0 for i in range(28)] for j in range(28)]
        for i in range(28):
            for j in range(28):
                # pixel_image[i][j] = pix[i, j]
                x.append(pix[i, j])
        assert self.get_dimension() == len(x), \
            "Dimension of %s should be %i, but was %i" % \
            (self.__str__(), self.get_dimension(), len(x))
        return x


class Ink(object):

    """Ink as a 1 dimensional feature. It gives a numeric value for the amount
       of ink this would eventually have consumed.
    """

    normalize = True

    def __repr__(self):
        return "Ink"

    def __str__(self):
        return "ink"

    def get_dimension(self):
        return 1

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        ink = 0.
        # calculate ink used for this symbol
        # TODO: What about dots? What about speed?
        for stroke in handwritten_data.get_pointlist():
            last_point = None
            for point in stroke:
                if last_point is not None:
                    ink += preprocessing._euclidean_distance(last_point, point)
                last_point = point
        return [ink]


class AspectRatio(object):

    """Aspect ratio of a recording as a 1 dimensional feature."""

    normalize = True

    def __repr__(self):
        return "Aspect Ratio"

    def __str__(self):
        return "Aspect Ratio"

    def get_dimension(self):
        return 1

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        width = float(handwritten_data.get_width()+0.01)
        height = float(handwritten_data.get_height()+0.01)
        return [width/height]


class Width(object):

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

    def get_dimension(self):
        return 1

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        return [float(handwritten_data.get_width())]


class Height(object):

    """Height of a recording as a a 1 dimensional feature.

    .. note::

        This is the current hight. So if the recording was scaled, this will not
        be the original height.
    """

    normalize = True

    def __repr__(self):
        return "Height"

    def __str__(self):
        return "Height"

    def get_dimension(self):
        return 1

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        return [float(handwritten_data.get_height())]


class Time(object):

    """The time in milliseconds it took to create the recording. This is a 1
       dimensional feature."""

    normalize = True

    def __repr__(self):
        return "Time"

    def __str__(self):
        return "Time"

    def get_dimension(self):
        """Get the dimension of the returned feature. This equals the number
           of elements in the returned list of numbers."""
        return 1

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        return [float(handwritten_data.get_time())]


class CenterOfMass(object):

    """Center of mass of a recording as a 2 dimensional feature."""

    normalize = True

    def __repr__(self):
        return "CenterOfMass"

    def __str__(self):
        return "Center of mass"

    def get_dimension(self):
        return 2

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        xs = []
        ys = []
        for stroke in handwritten_data.get_pointlist():
            for point in stroke:
                xs.append(point['x'])
                ys.append(point['y'])
        return [float(sum(xs))/len(xs), float(sum(ys))/len(ys)]


class StrokeCenter(object):

    """Get the stroke center of mass coordinates as a 2 dimensional feature."""

    normalize = True

    def __init__(self, strokes=4):
        self.strokes = strokes

    def __repr__(self):
        return "StrokeCenter"

    def __str__(self):
        return "Stroke center"

    def get_dimension(self):
        return self.strokes*2

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
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


class StrokeIntersections(object):
    """Count the number of intersections which strokes in the recording have
       with each other in form of a symmetrical matrix for the first
       `stroke=4` strokes. The feature dimension is
       :math:`round \frac{\text{strokes}^2}{2} + \frac{\text{strokes}}{2}`,
       because the symmetrical part is discarded.

    =======   ======= ======= ======= ===
      -       stroke1 stroke2 stroke3
    -------   ------- ------- ------- ---
    stroke1     0        1      0     ...
    stroke2     1        2      0     ...
    stroke3     0        0      0     ...
    =======   ======= ======= ======= ===

    Returns values of upper triangular matrix (including diagonal)
    from left to right, top to bottom.
    """

    normalize = True

    def __init__(self, strokes=4):
        self.strokes = strokes

    def __repr__(self):
        return "StrokeIntersections"

    def __str__(self):
        return "StrokeIntersections"

    def get_dimension(self):
        return int(round(float(self.strokes**2)/2 + float(self.strokes)/2))

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)

        def count_stroke_selfintersections(stroke):
            """ Get the number of self-intersections of a stroke."""
            # This can be solved more efficiently with sweep line
            counter = 0
            lines = []
            last = stroke[0]
            for point in stroke[1:]:
                line = LineString([(last['x'], last['y']),
                                   (point['x'], point['y'])])
                last = point
                lines.append((len(lines), line))

            for line1, line2 in itertools.combinations(lines, 2):
                index1, line1 = line1
                index2, line2 = line2
                if line1.intersects(line2) and abs(index1 - index2) > 1:
                    counter += 1
            return counter

        def count_intersections(stroke_a, stroke_b):
            # This can be solved more efficiently with sweep line
            counter = 0
            # build data structure a
            lines_a = []
            last = stroke_a[0]
            for point in stroke_a[1:]:
                line = LineString([(last['x'], last['y']),
                                   (point['x'], point['y'])])
                lines_a.append(line)
                last = point
            # build data structure b
            lines_b = []
            last = stroke_b[0]
            for point in stroke_b[1:]:
                line = LineString([(last['x'], last['y']),
                                   (point['x'], point['y'])])
                lines_b.append(line)
                last = point

            # Calculate intersections
            for line1, line2 in itertools.product(lines_a, lines_b):
                if line1.intersects(line2):
                    counter += 1
            return counter

        x = []
        pointlist = handwritten_data.get_pointlist()
        for i in range(self.strokes):
            for j in range(i, self.strokes):
                if len(pointlist) <= i or len(pointlist) <= j:
                    # There are less strokes! If there is no stroke, nothing
                    # can intersect
                    x.append(0)
                else:
                    # Does stroke i intersect stroke j?
                    if i == j:
                        x.append(count_stroke_selfintersections(pointlist[i]))
                    else:
                        x.append(count_intersections(pointlist[i],
                                                     pointlist[j]))
        # print("%s - %i" % (handwritten_data.formula_in_latex,
        #                    handwritten_data.raw_data_id))
        # curr = 0
        # for i in range(self.strokes, 0, -1):
        #     line = "\t"*(self.strokes - i)
        #     for j in range(i):
        #         line += str(x[curr]) + "\t"
        #         curr += 1

        assert self.get_dimension() == len(x), \
            "Dimension of %s should be %i, but was %i" % \
            (self.__str__(), self.get_dimension(), len(x))
        return x


class ReCurvature(object):

    """Re-curvature is a 1 dimensional, stroke-global feature for a recording.
       It is the ratio
       :math:`\frac{\text{height}(s)}{\text{distance}(s[0], s[-1])}`.
    """

    normalize = True

    def __init__(self, strokes=4):
        self.strokes = strokes

    def __repr__(self):
        return "ReCurvature"

    def __str__(self):
        return "Re-curvature"

    def get_dimension(self):
        return self.strokes

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        x = []
        for stroke in handwritten_data.get_pointlist():
            stroke_y = [point['y'] for point in stroke]
            height = max(stroke_y) - min(stroke_y)
            length = 0.0
            last_point = stroke[0]
            for point in stroke[1:]:
                length += preprocessing._euclidean_distance(point, last_point)
                last_point = point

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
            (self.__str__(), self.get_dimension(), len(x))
        return x


if __name__ == '__main__':
    import doctest
    doctest.testmod()
