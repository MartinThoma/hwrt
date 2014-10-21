#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Preprocessing algorithms.

Each algorithm works on the HandwrittenData class. They have to be applied like
this:

 >>> a = HandwrittenData(...)
 >>> preprocessing_queue = [Scale_and_shift(), \
                           Stroke_connect(), \
                           Douglas_peucker(EPSILON=0.2), \
                           Space_evenly(number=100)]
 >>> a.preprocessing(preprocessing_queue)
"""

import numpy
import inspect
from scipy.interpolate import interp1d
import math
import logging
import sys
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)
# mine
import HandwrittenData


def _euclidean_distance(p1, p2):
    """Calculate the euclidean distance of two 2D points."""
    return math.sqrt((p1["x"]-p2["x"])**2 + (p1["y"]-p2["y"])**2)


def _flatten(two_dimensional_list):
    """Flatten a 2D list into a 1D list"""
    return [i for inner_list in two_dimensional_list for i in inner_list]


def get_class(name):
    """Get function pointer by string."""
    clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    for string_name, act_class in clsmembers:
        if string_name == name:
            return act_class
    logging.debug("Unknown class '%s'.", name)
    return None


def get_preprocessing_queue(model_description_preprocessing):
    """Get preprocessing queue from a list of dictionaries

    >>> l = [{'Remove_duplicate_time': None}, \
             {'Scale_and_shift': [{'center': True}]} \
            ]
    >>> get_preprocessing_queue(l)
    [Remove_duplicate_time, Scale_and_shift
     - center: True
     - max_width: 1
     - max_height: 1
    ]
    """
    preprocessing_queue = []
    for preprocessing in model_description_preprocessing:
        for alg, params in preprocessing.items():
            alg = get_class(alg)
            if params is None:
                preprocessing_queue.append(alg())
            else:
                parameters = {}
                for dicts in params:
                    for param_name, param_value in dicts.items():
                        parameters[param_name] = param_value
                preprocessing_queue.append(alg(**parameters))
    return preprocessing_queue

# Only preprocessing classes follow
# Everyone must have a __str__, __repr__ and __call__
# where
# * __call__ must take exactly one argument of type HandwrittenData
# * __call__ must call the Handwriting.set_points


class Remove_duplicate_time(object):
    """If a recording has two points with the same timestamp, than the second
       one will be discarded."""
    def __repr__(self):
        return "Remove_duplicate_time"

    def __str__(self):
        return "remove duplicate time"

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        pointlist = handwritten_data.get_pointlist()
        new_pointlist = []
        t = []
        for stroke in pointlist:
            new_stroke = []
            for point in stroke:
                if point['time'] not in t:
                    new_stroke.append(point)
                    t.append(point['time'])
            if len(new_stroke) > 0:
                new_pointlist.append(new_stroke)
        # Make sure there are no duplicates
        times = [point['time'] for stroke in new_pointlist for point in stroke]
        assert len(times) == len(set(times)), \
            ("The list of all times in Remove_duplicate_time has %i values, "
             "but the set has %i values: %s --- %s") % \
            (len(times), len(set(times), pointlist, new_pointlist))
        handwritten_data.set_pointlist(new_pointlist)


class Remove_points(object):
    """Remove all single point strokes from the recording, except if
       the whole recording consists of points only.
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


class Scale_and_shift(object):
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
        return ("Scale_and_shift\n"
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

    def get_scale_and_shift_parameters(self, handwritten_data):
        """ Take a list of points and calculate the factors for scaling and
            moving it so that it's in the unit square. Keept the aspect
            ratio.
            Optionally center the points inside of the unit square.
        """
        a = handwritten_data.get_bounding_box()

        width = a['maxx'] - a['minx'] + self.width_add
        height = a['maxy'] - a['miny'] + self.height_add

        factorX, factorY = 1, 1
        if width != 0:
            factorX = self.max_width/width

        if height != 0:
            factorY = self.max_height/height

        factor = min(factorX, factorY)
        addx, addy = 0, 0

        if self.center:
            # Only one dimension (x or y) has to be centered (the smaller one)
            add = -(factor/(2*max(factorX, factorY)))

            if factor == factorX:
                addy = add
                if self.center_other:
                    addx = -(width*factor/2.0)
            else:
                addx = add
                if self.center_other:
                    addy = -(height*factor/2.0)

        return {"factor": factor, "addx": addx, "addy": addy,
                "minx": a['minx'], "miny": a['miny'], "mint": a['mint']}

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)

        tmp = self.get_scale_and_shift_parameters(handwritten_data)
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


class Space_evenly(object):
    """Space the points evenly in time over the complete recording. The
       parameter 'number' defines how many."""
    def __init__(self, number=100, kind='cubic'):
        self.number = number
        self.kind = kind

    def __repr__(self):
        return ("Space_evenly\n"
                " - number: %i\n"
                " - kind: %s\n") % \
            (self.number, self.kind)

    def __str__(self):
        return ("Space evenly\n"
                " - number: %i\n"
                " - kind: %s\n") % \
            (self.number, self.kind)

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        # Make sure that the lists are sorted
        pointlist = handwritten_data.get_sorted_pointlist()

        for i in range(len(pointlist)-1):
            # The last point of the previous stroke should be lower than the
            # first point of the next stroke
            assert (pointlist[i][-1]["time"] <= pointlist[i+1][0]["time"]), \
                ("Something is wrong with the time. The last point of "
                 "stroke %i has a time of %0.2f, but the first point of "
                 "stroke %i has a time of %0.2f. See raw_data_id %s") % \
                (i,
                 pointlist[i][-1]["time"],
                 i+1,
                 pointlist[i+1][0]["time"],
                 str(handwritten_data.raw_data_id))

        # calculate "pen_down" strokes
        times = []
        for i, stroke in enumerate(pointlist):
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

        # Model "pen_up" strokes
        for i in range(len(pointlist) - 1):
            stroke_info = {"start": pointlist[i][-1],
                           "end": pointlist[i+1][0],
                           "pen_down": False}
            x, y, t = [], [], []
            for point in [pointlist[i][-1], pointlist[i+1][0]]:
                if point['time'] not in t:
                    x.append(point['x'])
                    y.append(point['y'])
                    t.append(point['time'])
                else:
                    # TODO: That should not happen
                    pass
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

        new_pointlist = []

        tnew = numpy.linspace(pointlist[0][0]['time'],
                              pointlist[-1][-1]['time'],
                              self.number)

        for time in tnew:
            for stroke_intervall in times:
                if stroke_intervall["start"] <= time <= stroke_intervall["end"]:
                    x = float(stroke_intervall['fx'](time))
                    y = float(stroke_intervall['fy'](time))
                    time = float(time)
                    new_pointlist.append({'x': x, 'y': y, 'time': time,
                                          'pen_down':
                                          stroke_intervall['pen_down']})
        handwritten_data.set_pointlist([new_pointlist])


class Space_evenly_per_stroke(object):
    """Space the points evenly for every single stroke seperatly."""
    def __init__(self, number=100, kind='cubic'):
        self.number = number
        self.kind = kind

    def __repr__(self):
        return ("Space_evenly_per_stroke\n"
                " - number: %i\n"
                " - kind: %s\n") % \
            (self.number, self.kind)

    def __str__(self):
        return ("Space evenly per stroke\n"
                " - number: %i\n"
                " - kind: %s\n") % \
            (self.number, self.kind)

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        pointlist = handwritten_data.get_sorted_pointlist()
        new_pointlist = []

        for stroke in pointlist:
            new_stroke = []
            if len(stroke) < 2:
                # Don't do anything if there are less than 2 points
                new_stroke = stroke
            elif 2 <= len(stroke) <= 3:
                # Linear interpolation for 2 or 3 points
                # TODO: This is much code duplication. Can this be done better?
                stroke = sorted(stroke, key=lambda p: p['time'])

                x, y, t = [], [], []

                for point in stroke:
                    x.append(point['x'])
                    y.append(point['y'])
                    t.append(point['time'])

                x, y = numpy.array(x), numpy.array(y)
                failed = False
                try:
                    fx = interp1d(t, x, kind='linear')
                    fy = interp1d(t, y, kind='linear')
                except Exception as e:
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
                        raise e

                for x, y, t in zip(fx(tnew), fy(tnew), tnew):
                    new_stroke.append({'x': x, 'y': y, 'time': t})
            else:
                x, y, t = [], [], []

                for point in stroke:
                    x.append(point['x'])
                    y.append(point['y'])
                    t.append(point['time'])

                x, y = numpy.array(x), numpy.array(y)
                failed = False
                try:
                    fx = interp1d(t, x, kind=self.kind)
                    fy = interp1d(t, y, kind=self.kind)
                except Exception as e:
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
            new_pointlist.append(new_stroke)
        handwritten_data.set_pointlist(new_pointlist)


class Douglas_peucker(object):
    """Apply the Douglas-Peucker algorithm to each stroke of pointlist
       seperately.
    """
    def __init__(self, EPSILON):
        self.EPSILON = EPSILON

    def __repr__(self):
        return "Douglas_peucker (EPSILON: %0.2f)\n" % self.EPSILON

    def __str__(self):
        return "Douglas_peucker (EPSILON: %0.2f)\n" % self.EPSILON

    def DouglasPeucker(self, PointList, EPSILON):
        def LotrechterAbstand(p3, p1, p2):
            """
            Calculate the distance from p3 to the stroke defined by p1 and p2.
            :param p1: start of stroke
            :type p1: dictionary with "x" and "y"
            :param p2: end of stroke
            :type p2: dictionary with "x" and "y"
            :param p3: point
            :type p3: dictionary with "x" and "y"
            """
            x3 = p3['x']
            y3 = p3['y']

            px = p2['x']-p1['x']
            py = p2['y']-p1['y']

            something = px*px + py*py
            if (something == 0):
                # TODO: really?
                return 0

            u = ((x3 - p1['x']) * px + (y3 - p1['y']) * py) / something

            if u > 1:
                u = 1
            elif u < 0:
                u = 0

            x = p1['x'] + u * px
            y = p1['y'] + u * py

            dx = x - x3
            dy = y - y3

            # Note: If the actual distance does not matter,
            # if you only want to compare what this function
            # returns to other results of this function, you
            # can just return the squared distance instead
            # (i.e. remove the sqrt) to gain a little performance

            dist = math.sqrt(dx*dx + dy*dy)
            return dist

        # Finde den Punkt mit dem größten Abstand
        dmax = 0
        index = 0
        for i in range(1, len(PointList)):
            d = LotrechterAbstand(PointList[i], PointList[0], PointList[-1])
            if d > dmax:
                index = i
                dmax = d

        # Wenn die maximale Entfernung größer als EPSILON ist, dann rekursiv
        # vereinfachen
        if dmax >= EPSILON:
            # Recursive call
            recResults1 = self.DouglasPeucker(PointList[0:index], EPSILON)
            recResults2 = self.DouglasPeucker(PointList[index:], EPSILON)

            # Ergebnisliste aufbauen
            ResultList = recResults1[:-1] + recResults2
        else:
            ResultList = [PointList[0], PointList[-1]]

        # Ergebnis zurückgeben
        return ResultList

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        pointlist = handwritten_data.get_pointlist()

        for i in range(0, len(pointlist)):
            pointlist[i] = self.DouglasPeucker(pointlist[i], self.EPSILON)
        handwritten_data.set_pointlist(pointlist)
        # This might have duplicated points! Filter them!
        handwritten_data.preprocessing([Remove_duplicate_time()])


class Stroke_connect(object):
    """Detect if strokes were probably accidentially disconnected. If that is
       the case, connect them.
    """
    def __init__(self, minimum_distance=0.05):
        self.minimum_distance = minimum_distance

    def __repr__(self):
        return "Stroke_connect (minimum_distance: %0.2f)" % \
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
                if _euclidean_distance(last_point, first_point) < \
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


class Dot_reduction(object):
    """Reduce strokes where the maximum distance between points is below a
       threshold to a single dot.
    """
    def __init__(self, threshold):
        self.threshold = threshold

    def __repr__(self):
        return "Dot_reduction (threshold: %0.2f)" % \
            self.threshold

    def __str__(self):
        return "Dot_reduction (threshold: %0.2f)" % \
            self.threshold

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)

        def get_max_distance(L):
            """Find the maximum distance between two points in a list of points
            :param L: list of points
            :type L: list
            :returns: maximum distance bewtween two points
            :rtype: float
            """
            if len(L) <= 1:
                return -1
            else:
                max_dist = _euclidean_distance(L[0], L[1])
                for i in range(len(L)-1):
                    for j in range(i+1, len(L)):
                        max_dist = max(_euclidean_distance(L[i], L[j]),
                                       max_dist)
                return max_dist

        def get_average_point(L):
            """Calculate the average point.
            :param L: list of points
            :type L: list
            :returns: a single point
            :rtype: dict
            """
            x, y, t = 0, 0, 0
            for point in L:
                x += point['x']
                y += point['y']
                t += point['time']
            x = float(x) / len(L)
            y = float(y) / len(L)
            t = float(t) / len(L)
            return {'x': x, 'y': y, 'time': t}

        new_pointlist = []
        pointlist = handwritten_data.get_pointlist()
        for stroke in pointlist:
            new_stroke = stroke
            if len(stroke) > 1 and get_max_distance(stroke) < self.threshold:
                new_stroke = [get_average_point(stroke)]
            new_pointlist.append(new_stroke)

        handwritten_data.set_pointlist(new_pointlist)


class Wild_point_filter(object):
    """Find wild points and remove them. The threshold means
       speed in pixels / ms.
    """
    def __init__(self, threshold):
        """The threshold is a speed threshold"""
        self.threshold = threshold

    def __repr__(self):
        return "Wild_point_filter"

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


class Weighted_average_smoothing(object):
    """Smooth every stroke by a weighted average."""
    def __init__(self, theta):
        """Theta is a list of 3 non-negative numbers"""
        assert len(theta) == 3, \
            "theta has length %i, but should have length 3" % \
            len(theta)
        theta = map(float, theta)
        # Normalize parameters to a sum of 1
        self.theta = list(1./sum(theta) * numpy.array(theta))

    def __repr__(self):
        return "Weighted_average_smoothing"

    def __str__(self):
        return "Weighted average smoothing (theta: %s)" % \
            self.theta

    def calculate_average(self, points):
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
                    p = self.calculate_average(points)
                    new_pointlist[-1].append(p)
                new_pointlist[-1].append(stroke[-1])
        handwritten_data.set_pointlist(new_pointlist)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
