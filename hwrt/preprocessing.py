#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Preprocessing algorithms.

Each algorithm works on the HandwrittenData class. They have to be applied like
this:

    >>> a = HandwrittenData(...)
    >>> preprocessing_queue = [ScaleAndShift(),
                               StrokeConnect(),
                               DouglasPeucker(epsilon=0.2),
                               SpaceEvenly(number=100)]
    >>> a.preprocessing(preprocessing_queue)
"""

import logging
import sys
import numpy
from scipy.interpolate import interp1d
import math

# hwrt modules
from . import HandwrittenData
from . import utils
from . import geometry


def euclidean_distance(p1, p2):
    """Calculate the euclidean distance of two 2D points.

    >>> euclidean_distance({'x': 0, 'y': 0}, {'x': 0, 'y': 3})
    3.0
    >>> euclidean_distance({'x': 0, 'y': 0}, {'x': 0, 'y': -3})
    3.0
    >>> euclidean_distance({'x': 0, 'y': 0}, {'x': 3, 'y': 4})
    5.0
    """
    return math.sqrt((p1["x"]-p2["x"])**2 + (p1["y"]-p2["y"])**2)


def get_preprocessing_queue(preprocessing_list):
    """Get preprocessing queue from a list of dictionaries

    >>> l = [{'RemoveDuplicateTime': None},
             {'ScaleAndShift': [{'center': True}]}
            ]
    >>> get_preprocessing_queue(l)
    [RemoveDuplicateTime, ScaleAndShift
     - center: True
     - max_width: 1
     - max_height: 1
    ]
    """
    return utils.get_objectlist(preprocessing_list,
                                config_key='preprocessing',
                                module=sys.modules[__name__])


def print_preprocessing_list(preprocessing_queue):
    """
    Print the ``preproc_list`` in a human-readable form.

    Parameters
    ----------
    preprocessing_queue : list of preprocessing objects
        Algorithms that get applied for preprocessing.
    """
    print("## Preprocessing")
    print("```")
    for algorithm in preprocessing_queue:
        print("* " + str(algorithm))
    print("```")

# Only preprocessing classes follow
# Everyone must have a __str__, __repr__ and __call__
# where
# * __call__ must take exactly one argument of type HandwrittenData
# * __call__ must call the Handwriting.set_points


class RemoveDuplicateTime(object):
    """If a recording has two points with the same timestamp, than the second
       point will be discarded. This is useful for a couple of algorithms that
       don't expect two points at the same time."""
    def __repr__(self):
        return "RemoveDuplicateTime"

    def __str__(self):
        return "remove duplicate time"

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        pointlist = handwritten_data.get_pointlist()
        new_pointlist = []
        times = []
        for stroke in pointlist:
            new_stroke = []
            for point in stroke:
                if point['time'] not in times:
                    new_stroke.append(point)
                    times.append(point['time'])
            if len(new_stroke) > 0:
                new_pointlist.append(new_stroke)
        # Make sure there are no duplicates
        times = [point['time'] for stroke in new_pointlist for point in stroke]
        assert len(times) == len(set(times)), \
            ("The list of all times in RemoveDuplicateTime has %i values, "
             "but the set has %i values: %s --- %s") % \
            (len(times), len(set(times)), pointlist, new_pointlist)
        handwritten_data.set_pointlist(new_pointlist)


class RemoveDots(object):
    """Remove all strokes that have only a single point (a dot) from the
       recording, except if the whole recording consists of dots only.
    """
    def __repr__(self):
        return "Remove_points"

    def __str__(self):
        return "remove points"

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        pointlist = handwritten_data.get_pointlist()
        has_nonpoint_stroke = False
        # Check if recording has non-point stroke:
        for stroke in pointlist:
            if len(stroke) > 1:
                has_nonpoint_stroke = True
        if has_nonpoint_stroke:
            new_pointlist = []
            for stroke in pointlist:
                if len(stroke) > 1:
                    new_pointlist.append(stroke)
            handwritten_data.set_pointlist(new_pointlist)


class ScaleAndShift(object):
    """ Scale a recording so that it fits into a unit square. This keeps the
        aspect ratio. Then the recording is shifted. The default way is to
        shift it so that the recording is in [0, 1] × [0,1]. However, it
        can also be used to be centered within [-1, 1] × [-1, 1] around the
        origin (0, 0) by setting center=True and center_other=True.
    """
    def __init__(self, center=False, max_width=1., max_height=1.,
                 width_add=0, height_add=0, center_other=False):
        self.center = center
        self.max_width = max_width
        self.max_height = max_height
        self.width_add = width_add
        self.height_add = height_add
        self.center_other = center_other

    def __repr__(self):
        return ("ScaleAndShift\n"
                " - center: %r\n"
                " - max_width: %i\n"
                " - max_height: %i\n") % \
            (self.center, self.max_width, self.max_height)

    def __str__(self):
        return ("Scale and shift\n"
                " - center: %r\n"
                " - max_width: %i\n"
                " - max_height: %i\n") % \
            (self.center, self.max_width, self.max_height)

    def _get_parameters(self, handwritten_data):
        """ Take a list of points and calculate the factors for scaling and
            moving it so that it's in the unit square. Keept the aspect
            ratio.
            Optionally center the points inside of the unit square.
        """
        a = handwritten_data.get_bounding_box()

        width = a['maxx'] - a['minx'] + self.width_add
        height = a['maxy'] - a['miny'] + self.height_add

        factor_x, factor_y = 1, 1
        if width != 0:
            factor_x = self.max_width/width

        if height != 0:
            factor_y = self.max_height/height

        factor = min(factor_x, factor_y)
        addx, addy = 0.0, 0.0

        if self.center:
            # Only one dimension (x or y) has to be centered (the smaller one)
            add = -(factor/(2.0*max(factor_x, factor_y)))

            if factor == factor_x:
                addy = add
                if self.center_other:
                    addx = -(width*factor/2.0)
            else:
                addx = add
                if self.center_other:
                    addy = -(height*factor/2.0)
        assert factor > 0, "factor > 0 is False. factor = %s" % str(factor)
        assert isinstance(addx, float), "addx is %s" % str(addx)
        assert isinstance(addy, float), "addy is %s" % str(addy)
        assert isinstance(a['minx'], (int, float)), "minx is %s" % str(a['minx'])
        assert isinstance(a['miny'], (int, float)), "miny is %s" % str(a['miny'])
        assert isinstance(a['mint'], (int, float)), "mint is %s" % str(a['mint'])
        return {"factor": factor, "addx": addx, "addy": addy,
                "minx": a['minx'], "miny": a['miny'], "mint": a['mint']}

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)

        tmp = self._get_parameters(handwritten_data)
        factor, addx, addy = tmp['factor'], tmp['addx'], tmp['addy']
        minx, miny, mint = tmp['minx'], tmp['miny'], tmp['mint']

        pointlist = handwritten_data.get_pointlist()
        for strokenr, stroke in enumerate(pointlist):
            for key, p in enumerate(stroke):
                pointlist[strokenr][key] = {
                    "x": (p["x"] - minx) * factor + addx,
                    "y": (p["y"] - miny) * factor + addy,
                    "time": p["time"] - mint}
                if "pen_down" in p:
                    pointlist[strokenr][key]["pen_down"] = p["pen_down"]
        handwritten_data.set_pointlist(pointlist)
        assert self.max_width - handwritten_data.get_width() >= -0.00001, \
            "max_width: %0.5f; width: %0.5f" % (self.max_width,
                                                handwritten_data.get_width())
        assert self.max_height - handwritten_data.get_height() >= -0.00001, \
            "max_height: %0.5f; height: %0.5f" % \
            (self.max_height, handwritten_data.get_height())


class SpaceEvenly(object):
    """Space the points evenly in time over the complete recording. The
       parameter 'number' defines how many."""
    def __init__(self, number=100, kind='cubic'):
        self.number = number
        self.kind = kind

    def __repr__(self):
        return ("SpaceEvenly\n"
                " - number: %i\n"
                " - kind: %s\n") % \
            (self.number, self.kind)

    def __str__(self):
        return ("Space evenly\n"
                " - number: %i\n"
                " - kind: %s\n") % \
            (self.number, self.kind)

    def _calculate_pen_down_strokes(self, pointlist, times=None):
        """Calculate the intervall borders 'times' that contain the information
           when a stroke started, when it ended and how it should be
           interpolated."""
        if times is None:
            times = []
        for stroke in pointlist:
            stroke_info = {"start": stroke[0]['time'],
                           "end": stroke[-1]['time'],
                           "pen_down": True}
            # set up variables for interpolation
            x, y, t = [], [], []
            for point in stroke:
                if point['time'] not in t:
                    x.append(point['x'])
                    y.append(point['y'])
                    t.append(point['time'])
            x, y = numpy.array(x), numpy.array(y)
            if len(t) == 1:
                # constant interpolation
                fx, fy = lambda x: float(x), lambda y: float(y)
            elif len(t) == 2:
                # linear interpolation
                fx, fy = interp1d(t, x, 'linear'), interp1d(t, y, 'linear')
            elif len(t) == 3:
                # quadratic interpolation
                fx = interp1d(t, x, 'quadratic')
                fy = interp1d(t, y, 'quadratic')
            else:
                fx, fy = interp1d(t, x, self.kind), interp1d(t, y, self.kind)
            stroke_info['fx'] = fx
            stroke_info['fy'] = fy
            times.append(stroke_info)
        return times

    def _calculate_pen_up_strokes(self, pointlist, times=None):
        """ 'Pen-up' strokes are virtual strokes that were not drawn. It
            models the time when the user moved from one stroke to the next.
        """
        if times is None:
            times = []
        for i in range(len(pointlist) - 1):
            stroke_info = {"start": pointlist[i][-1]['time'],
                           "end": pointlist[i+1][0]['time'],
                           "pen_down": False}
            x, y, t = [], [], []
            for point in [pointlist[i][-1], pointlist[i+1][0]]:
                if point['time'] not in t:
                    x.append(point['x'])
                    y.append(point['y'])
                    t.append(point['time'])
            if len(x) == 1:
                # constant interpolation
                fx, fy = lambda x: float(x), lambda y: float(y)
            else:
                # linear interpolation
                x, y = numpy.array(x), numpy.array(y)
                fx = interp1d(t, x, kind='linear')
                fy = interp1d(t, y, kind='linear')
            stroke_info['fx'] = fx
            stroke_info['fy'] = fy
            times.append(stroke_info)
        return times

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        # Make sure that the lists are sorted
        pointlist = handwritten_data.get_sorted_pointlist()

        # Build 'times' datastructure which will contain information about
        # strokes and when they were started / ended and how they should be
        # interpolated
        times = self._calculate_pen_down_strokes(pointlist)
        times = self._calculate_pen_up_strokes(pointlist, times)

        tnew = numpy.linspace(pointlist[0][0]['time'],
                              pointlist[-1][-1]['time'],
                              self.number)

        # Create the new pointlist
        new_pointlist = []
        for time in tnew:
            for stroke_interval in times:
                if stroke_interval["start"] <= time <= stroke_interval["end"]:
                    x = float(stroke_interval['fx'](time))
                    y = float(stroke_interval['fy'](time))
                    time = float(time)
                    new_pointlist.append({'x': x, 'y': y, 'time': time,
                                          'pen_down':
                                          stroke_interval['pen_down']})
        handwritten_data.set_pointlist([new_pointlist])


class SpaceEvenlyPerStroke(object):
    """Space the points evenly for every single stroke separately. The
       parameter `number` defines how many points are used per stroke and the
       parameter `kind` defines which kind of interpolation is used. Possible
       values include `cubic`, `quadratic`, `linear`, `nearest`. This part of
       the implementation relies on
       :mod:`scipy.interpolate.interp1d <scipy:scipy.interpolate.interp1d>`.
    """
    def __init__(self, number=100, kind='cubic'):
        self.number = number
        self.kind = kind

    def __repr__(self):
        return ("SpaceEvenlyPerStroke\n"
                " - number: %i\n"
                " - kind: %s\n") % \
            (self.number, self.kind)

    def __str__(self):
        return ("Space evenly per stroke\n"
                " - number: %i\n"
                " - kind: %s\n") % \
            (self.number, self.kind)

    def _space(self, handwritten_data, stroke, kind):
        """Do the interpolation of 'kind' for 'stroke'"""
        new_stroke = []
        stroke = sorted(stroke, key=lambda p: p['time'])

        x, y, t = [], [], []

        for point in stroke:
            x.append(point['x'])
            y.append(point['y'])
            t.append(point['time'])

        x, y = numpy.array(x), numpy.array(y)
        failed = False
        try:
            fx = interp1d(t, x, kind=kind)
            fy = interp1d(t, y, kind=kind)
        except Exception as e:  # pylint: disable=W0703
            if handwritten_data.raw_data_id is not None:
                logging.debug("spline failed for raw_data_id %i",
                              handwritten_data.raw_data_id)
            else:
                logging.debug("spline failed")
            logging.debug(e)
            failed = True

        tnew = numpy.linspace(t[0], t[-1], self.number)

        # linear interpolation fallback due to
        # https://github.com/scipy/scipy/issues/3868
        if failed:
            try:
                fx = interp1d(t, x, kind='linear')
                fy = interp1d(t, y, kind='linear')
                failed = False
            except Exception as e:
                logging.debug("len(stroke) = %i", len(stroke))
                logging.debug("len(x) = %i", len(x))
                logging.debug("len(y) = %i", len(y))
                logging.debug("stroke=%s", stroke)
                raise e

        for x, y, t in zip(fx(tnew), fy(tnew), tnew):
            new_stroke.append({'x': x, 'y': y, 'time': t})
        return new_stroke

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        pointlist = handwritten_data.get_sorted_pointlist()
        new_pointlist = []

        for stroke in pointlist:
            if len(stroke) < 2:
                # Don't do anything if there are less than 2 points
                new_stroke = stroke
            elif 2 <= len(stroke) <= 3:
                # Linear interpolation for 2 or 3 points
                new_stroke = self._space(handwritten_data,
                                         stroke,
                                         'linear')
            else:
                new_stroke = self._space(handwritten_data,
                                         stroke,
                                         self.kind)
            new_pointlist.append(new_stroke)
        handwritten_data.set_pointlist(new_pointlist)


class DouglasPeucker(object):
    """Apply the Douglas-Peucker stroke simplification algorithm separately to
       each stroke of the recording. The algorithm has a threshold parameter
       `epsilon` that indicates how much the stroke is simplified. The smaller
       the parameter, the closer will the resulting strokes be to the original.
    """
    def __init__(self, epsilon=0.2):
        self.epsilon = epsilon

    def __repr__(self):
        return "DouglasPeucker (epsilon: %0.2f)\n" % self.epsilon

    def __str__(self):
        return "DouglasPeucker (epsilon: %0.2f)\n" % self.epsilon

    def _stroke_simplification(self, pointlist):
        """The Douglas-Peucker line simplification takes a list of points as an
           argument. It tries to simplifiy this list by removing as many points
           as possible while still maintaining the overall shape of the stroke.
           It does so by taking the first and the last point, connecting them
           by a straight line and searchin for the point with the highest
           distance. If that distance is bigger than 'epsilon', the point is
           important and the algorithm continues recursively."""

        # Find the point with the biggest distance
        dmax = 0
        index = 0
        for i in range(1, len(pointlist)):
            d = geometry.perpendicular_distance(pointlist[i],
                                                pointlist[0],
                                                pointlist[-1])
            if d > dmax:
                index = i
                dmax = d

        # If the maximum distance is bigger than the threshold 'epsilon', then
        # simplify the pointlist recursively
        if dmax >= self.epsilon:
            # Recursive call
            rec_results1 = self._stroke_simplification(pointlist[0:index])
            rec_results2 = self._stroke_simplification(pointlist[index:])
            result_list = rec_results1[:-1] + rec_results2
        else:
            result_list = [pointlist[0], pointlist[-1]]

        return result_list

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        pointlist = handwritten_data.get_pointlist()

        for i in range(0, len(pointlist)):
            pointlist[i] = self._stroke_simplification(pointlist[i])
        handwritten_data.set_pointlist(pointlist)
        # This might have duplicated points! Filter them!
        handwritten_data.preprocessing([RemoveDuplicateTime()])


class StrokeConnect(object):
    """`StrokeConnect`: Detect if strokes were probably accidentally
       disconnected. If that is the case, connect them. This is detected by the
       threshold parameter `minimum_distance`. If the distance between the end
       point of a stroke and the first point of the next stroke is below the
       minimum distance, the strokes will be connected.
    """
    def __init__(self, minimum_distance=0.05):
        self.minimum_distance = minimum_distance

    def __repr__(self):
        return "StrokeConnect (minimum_distance: %0.2f)" % \
            self.minimum_distance

    def __str__(self):
        return "Stroke connect (minimum_distance: %0.2f)" % \
            self.minimum_distance

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        pointlist = handwritten_data.get_pointlist()

        # Connecting strokes makes only sense when there are multiple strokes
        if len(pointlist) > 1:
            strokes = []
            last_appended = False
            i = 0
            while i < len(pointlist)-1:
                last_point = pointlist[i][-1]
                first_point = pointlist[i+1][0]
                if euclidean_distance(last_point, first_point) < \
                   self.minimum_distance:
                    strokes.append(pointlist[i]+pointlist[i+1])
                    pointlist[i+1] = strokes[-1]
                    if i == len(pointlist)-2:
                        last_appended = True
                    i += 1
                else:
                    strokes.append(pointlist[i])
                i += 1
            if not last_appended:
                strokes.append(pointlist[-1])
            handwritten_data.set_pointlist(strokes)


class DotReduction(object):
    """
    Reduce strokes where the maximum distance between points is below a
    `threshold` to a single dot.
    """
    def __init__(self, threshold=5):
        self.threshold = threshold

    def __repr__(self):
        return "DotReduction (threshold: %0.2f)" % \
            self.threshold

    def __str__(self):
        return "DotReduction (threshold: %0.2f)" % \
            self.threshold

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)

        def _get_max_distance(L):
            """
            Find the maximum distance between two points in a list of points

            Parameters
            ----------
            L : list
                list of points

            Returns
            -------
            float
                maximum distance bewtween two points
            """
            if len(L) <= 1:
                return -1
            else:
                max_dist = euclidean_distance(L[0], L[1])
                for i in range(len(L)-1):
                    for j in range(i+1, len(L)):
                        max_dist = max(euclidean_distance(L[i], L[j]),
                                       max_dist)
                return max_dist

        def _get_average_point(pointlist):
            """
            Calculate the average point.

            Parameters
            ----------
            pointlist : list
                list of points

            Returns
            -------
            dict :
                a single point
            """
            x, y, t = 0, 0, 0
            for point in pointlist:
                x += point['x']
                y += point['y']
                t += point['time']
            x = float(x) / len(pointlist)
            y = float(y) / len(pointlist)
            t = float(t) / len(pointlist)
            return {'x': x, 'y': y, 'time': t}

        new_pointlist = []
        pointlist = handwritten_data.get_pointlist()
        for stroke in pointlist:
            new_stroke = stroke
            if len(stroke) > 1 and _get_max_distance(stroke) < self.threshold:
                new_stroke = [_get_average_point(stroke)]
            new_pointlist.append(new_stroke)

        handwritten_data.set_pointlist(new_pointlist)


class WildPointFilter(object):
    """Find wild points and remove them. The threshold means
       speed in pixels / ms.
    """
    def __init__(self, threshold=3.0):
        """The threshold is a speed threshold"""
        self.threshold = threshold

    def __repr__(self):
        return "WildPointFilter"

    def __str__(self):
        return "Wild point filter (threshold: %0.2f)" % \
            self.threshold

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        new_pointlist = []
        pointlist = handwritten_data.get_sorted_pointlist()
        for stroke in pointlist:
            new_stroke = []
            for last_point, point in zip(stroke, stroke[1:]):
                space_dist = math.hypot(last_point['x'] - point['x'],
                                        last_point['y'] - point['y'])
                time_dist = float(point['time'] - last_point['time'])
                if time_dist == 0:
                    continue
                speed = space_dist/time_dist
                if speed < self.threshold:
                    new_stroke.append(point)

            new_pointlist.append(new_stroke)
        # Bounding box criterion:
        # If the distance from point to all others strokes bounding boxes is
        # more than 1/5 of the whole size, it is a wild point


class WeightedAverageSmoothing(object):
    """Smooth every stroke by a weighted average. This algorithm takes a list
       `theta` of 3 numbers that are the weights used for smoothing."""
    def __init__(self, theta=None):
        """Theta is a list of 3 non-negative numbers"""
        if theta is None:
            theta = [1./6, 4./6, 1./6]
        assert len(theta) == 3, \
            "theta has length %i, but should have length 3" % \
            len(theta)
        theta = [float(element) for element in theta]

        # Normalize parameters to a sum of 1
        self.theta = list(1./sum(theta) * numpy.array(theta))

    def __repr__(self):
        return "WeightedAverageSmoothing"

    def __str__(self):
        return "Weighted average smoothing (theta: %s)" % \
            self.theta

    def _calculate_average(self, points):
        """Calculate the arithmetic mean of the points x and y coordinates
           seperately.
        """
        assert len(self.theta) == len(points), \
            "points has length %i, but should have length %i" % \
            (len(points), len(self.theta))
        new_point = {'x': 0, 'y': 0, 'time': 0}
        for key in new_point:
            new_point[key] = self.theta[0] * points[0][key] + \
                self.theta[1] * points[1][key] + \
                self.theta[2] * points[2][key]
        return new_point

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        new_pointlist = []
        pointlist = handwritten_data.get_sorted_pointlist()
        for stroke in pointlist:
            tmp = [stroke[0]]
            new_pointlist.append(tmp)
            if len(stroke) > 1:
                for i in range(1, len(stroke)-1):
                    points = [stroke[i-1], stroke[i], stroke[i+1]]
                    p = self._calculate_average(points)
                    new_pointlist[-1].append(p)
                new_pointlist[-1].append(stroke[-1])
        handwritten_data.set_pointlist(new_pointlist)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
