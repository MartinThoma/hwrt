#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Representation of a recording of on-line handwritten data. On-line means
   that the pen trajectory is given (and not online as in 'Internet').
"""

import logging
import json


class HandwrittenData(object):
    """Represents a handwritten symbol."""
    def __init__(self, raw_data_json, formula_id=None, raw_data_id=None,
                 formula_in_latex=None, wild_point_count=0,
                 missing_stroke=0, user_id=0):
        self.raw_data_json = raw_data_json
        self.formula_id = formula_id
        self.raw_data_id = raw_data_id
        self.formula_in_latex = formula_in_latex
        self.wild_point_count = wild_point_count
        self.missing_stroke = missing_stroke
        self.user_id = user_id
        self.segmentation = None
        assert type(json.loads(self.raw_data_json)) is list, \
            "raw_data_json is not JSON: %r" % self.raw_data_json
        assert len(self.get_pointlist()) >= 1, \
            "The pointlist of formula_id %i is %s" % (self.formula_id,
                                                      self.get_pointlist())
        assert wild_point_count >= 0
        assert missing_stroke >= 0
        self.fix_times()

    def fix_times(self):
        """
        Some recordings have wrong times. Fix them so that nothing after
        loading a handwritten recording breaks.
        """
        pointlist = self.get_pointlist()
        times = [point['time'] for stroke in pointlist for point in stroke]
        times_min = max(min(times), 0)  # Make sure this is not None
        for i, stroke in enumerate(pointlist):
            for j, point in enumerate(stroke):
                if point['time'] is None:
                    pointlist[i][j]['time'] = times_min
                else:
                    times_min = point['time']
        self.raw_data_json = json.dumps(pointlist)

    def get_pointlist(self):
        """
        Get a list of lists of tuples from JSON raw data string. Those lists
        represent strokes with control points.

        Returns
        -------
        list :
            A list of strokes. Each stroke is a dictionary
            {'x': 123, 'y': 42, 'time': 1337}
        """
        try:
            pointlist = json.loads(self.raw_data_json)
        except Exception as inst:  # pragma: no cover
            logging.debug("pointStrokeList: strokelistP")
            logging.debug(self.raw_data_json)
            logging.debug("didn't work")
            raise inst

        if len(pointlist) == 0:  # pragma: no cover
            logging.warning("Pointlist was empty. Search for '" +
                            self.raw_data_json + "' in `wm_raw_draw_data`.")
        return pointlist

    def get_sorted_pointlist(self):
        """Make sure that the points and strokes are in order."""
        pointlist = self.get_pointlist()
        for i in range(len(pointlist)):
            pointlist[i] = sorted(pointlist[i], key=lambda p: p['time'])
        pointlist = sorted(pointlist, key=lambda stroke: stroke[0]['time'])
        return pointlist

    def set_pointlist(self, pointlist):
        """Overwrite pointlist.

        Parameters
        ----------
        pointlist : a list of strokes; each stroke is a list of points
            The inner lists represent strokes. Every stroke consists of points.
            Every point is a dictinary with 'x', 'y', 'time'.
        """
        assert type(pointlist) is list, \
            "pointlist is not of type list, but %r" % type(pointlist)
        assert len(pointlist) >= 1, \
            "The pointlist of formula_id %i is %s" % (self.formula_id,
                                                      self.get_pointlist())
        self.raw_data_json = json.dumps(pointlist)

    def get_bounding_box(self):
        """ Get the bounding box of a pointlist. """
        pointlist = self.get_pointlist()

        # Initialize bounding box parameters to save values
        minx, maxx = pointlist[0][0]["x"], pointlist[0][0]["x"]
        miny, maxy = pointlist[0][0]["y"], pointlist[0][0]["y"]
        mint, maxt = pointlist[0][0]["time"], pointlist[0][0]["time"]

        # Adjust parameters
        for stroke in pointlist:
            for p in stroke:
                minx, maxx = min(minx, p["x"]), max(maxx, p["x"])
                miny, maxy = min(miny, p["y"]), max(maxy, p["y"])
                mint, maxt = min(mint, p["time"]), max(maxt, p["time"])
        return {"minx": minx, "maxx": maxx, "miny": miny, "maxy": maxy,
                "mint": mint, "maxt": maxt}

    def get_width(self):
        """Get the width of the rectangular, axis-parallel bounding box."""
        box = self.get_bounding_box()
        return box['maxx'] - box['minx']

    def get_height(self):
        """Get the height of the rectangular, axis-parallel bounding box."""
        box = self.get_bounding_box()
        return box['maxy'] - box['miny']

    def get_area(self):
        """Get the area in square pixels of the recording."""
        return (self.get_height()+1) * (self.get_width()+1)

    def get_time(self):
        """Get the time in which the recording was created."""
        box = self.get_bounding_box()
        return box['maxt'] - box['mint']

    def preprocessing(self, algorithms):
        """Apply preprocessing algorithms.

        Parameters
        ----------
        algorithms : a list objects
            Preprocessing allgorithms which get applied in order.

        Examples
        --------
        >>> import preprocessing
        >>> a = HandwrittenData(...)
        >>> preprocessing_queue = [(preprocessing.scale_and_shift, []),
        ...                        (preprocessing.connect_strokes, []),
        ...                        (preprocessing.douglas_peucker,
        ...                         {'EPSILON': 0.2}),
        ...                        (preprocessing.space_evenly,
        ...                         {'number': 100,
        ...                          'KIND': 'cubic'})]
        >>> a.preprocessing(preprocessing_queue)
        """
        assert type(algorithms) is list
        for algorithm in algorithms:
            algorithm(self)

    def feature_extraction(self, algorithms):
        """Get a list of features.

        Every algorithm has to return the features as a list."""
        assert type(algorithms) is list
        features = []
        for algorithm in algorithms:
            new_features = algorithm(self)
            assert len(new_features) == algorithm.get_dimension(), \
                "Expected %i features from algorithm %s, got %i features" % \
                (algorithm.get_dimension(), str(algorithm), len(new_features))
            features += new_features
        return features

    def show(self):
        """Show the data graphically in a new pop-up window."""

        # prevent the following error:
        # '_tkinter.TclError: no display name and no $DISPLAY environment
        #    variable'
        # import matplotlib
        # matplotlib.use('GTK3Agg', warn=False)

        import matplotlib.pyplot as plt

        pointlist = self.get_pointlist()
        if 'pen_down' in pointlist[0][0]:
            assert len(pointlist) > 1, \
                "Lenght of pointlist was %i. Got: %s" % (len(pointlist),
                                                         pointlist)
            # Create a new pointlist that models pen-down strokes and pen
            # up strokes
            new_pointlist = []
            last_pendown_state = None
            stroke = []
            for point in pointlist[0]:
                if last_pendown_state is None:
                    last_pendown_state = point['pen_down']
                if point['pen_down'] != last_pendown_state:
                    new_pointlist.append(stroke)
                    last_pendown_state = point['pen_down']
                    stroke = []
                else:
                    stroke.append(point)
            new_pointlist.append(stroke)  # add the last stroke
            pointlist = new_pointlist

        _, ax = plt.subplots()
        ax.set_title("Raw data id: %s, "
                     "Formula_id: %s" % (str(self.raw_data_id),
                                         str(self.formula_id)))

        for stroke in pointlist:
            xs, ys = [], []
            for p in stroke:
                xs.append(p['x'])
                ys.append(p['y'])
            if "pen_down" in stroke[0] and stroke[0]["pen_down"] is False:
                plt.plot(xs, ys, '-x')
            else:
                plt.plot(xs, ys, '-o')
        plt.gca().invert_yaxis()
        ax.set_aspect('equal')
        plt.show()

    def count_single_dots(self):
        """Count all strokes of this recording that have only a single dot.
        """
        pointlist = self.get_pointlist()
        single_dots = 0
        for stroke in pointlist:
            if len(stroke) == 1:
                single_dots += 1
        return single_dots

    def get_center_of_mass(self):
        """
        Get a tuple (x,y) that is the center of mass. The center of mass is not
        necessarily the same as the center of the bounding box. Imagine a black
        square and a single dot wide outside of the square.
        """
        xsum, ysum, counter = 0., 0., 0
        for stroke in self.get_pointlist():
            for point in stroke:
                xsum += point['x']
                ysum += point['y']
                counter += 1
        return (xsum/counter, ysum/counter)

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "HandwrittenData(raw_data_id=%s)" % str(self.raw_data_id)

    def __str__(self):
        return repr(self)
