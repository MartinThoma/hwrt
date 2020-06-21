#!/usr/bin/env python

"""Representation of a recording of on-line handwritten data. On-line means
   that the pen trajectory is given (and not online as in 'Internet').
"""

# Core Library modules
import json
import logging
from typing import Callable, List

# Third party modules
import numpy
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


class HandwrittenData:
    """Represents a handwritten symbol."""

    def __init__(
        self,
        raw_data_json,
        formula_id=None,
        raw_data_id=None,
        formula_in_latex=None,
        wild_point_count=0,
        missing_stroke=0,
        user_id=0,
        user_name="",
        segmentation=None,
    ):
        self.raw_data_json = raw_data_json
        self.formula_id = formula_id
        self.raw_data_id = raw_data_id
        self.formula_in_latex = formula_in_latex
        self.wild_point_count = wild_point_count
        self.missing_stroke = missing_stroke
        self.user_id = user_id
        self.user_name = user_name
        self.segmentation = segmentation
        assert type(json.loads(self.raw_data_json)) is list, (
            "raw_data_json is not JSON list: %r" % self.raw_data_json
        )
        assert len(self.get_pointlist()) >= 1, (
            f"The pointlist of formula_id {self.formula_id} "
            f"is {self.get_pointlist()}"
        )
        if segmentation is None:
            # If no segmentation is given, assume all strokes belong to the
            # same symbol.
            self.segmentation = [
                [i for i in range(len(json.loads(self.raw_data_json)))]
            ]
        assert wild_point_count >= 0
        assert missing_stroke >= 0
        self.fix_times()

    @classmethod
    def generate(cls):
        """Generate a HandwrittenData object for testing and documentation."""
        return HandwrittenData(
            '[[{"x":678,"y":195,"time":1592756126416},'
            '{"x":677,"y":199,"time":1592756126420},'
            '{"x":675,"y":203,"time":1592756126427}]]'
        )

    def fix_times(self):
        """
        Some recordings have wrong times. Fix them so that nothing after
        loading a handwritten recording breaks.
        """
        pointlist = self.get_pointlist()
        times = [point["time"] for stroke in pointlist for point in stroke]
        times_min = max(min(times), 0)  # Make sure this is not None
        for i, stroke in enumerate(pointlist):
            for j, point in enumerate(stroke):
                if point["time"] is None:
                    pointlist[i][j]["time"] = times_min
                else:
                    times_min = point["time"]
        self.raw_data_json = json.dumps(pointlist)

    def get_pointlist(self):
        """
        Get a list of lists of tuples from JSON raw data string. Those lists
        represent strokes with control points.

        Returns
        -------
        list :
            A list of strokes. Each stroke is a list of dictionaries
            {'x': 123, 'y': 42, 'time': 1337}
        """
        try:
            pointlist = json.loads(self.raw_data_json)
        except Exception as inst:
            logger.debug("pointStrokeList: strokelistP")
            logger.debug(self.raw_data_json)
            logger.debug("didn't work")
            raise inst

        if len(pointlist) == 0:
            logger.warning(
                f"Pointlist was empty. Search for '{self.raw_data_json}' "
                f"in `wm_raw_draw_data`."
            )
        return pointlist

    def get_sorted_pointlist(self):
        """
        Make sure that the points and strokes are in order.

        Returns
        -------
        list
            A list of all strokes in the recording. Each stroke is represented
            as a list of dicts {'time': 123, 'x': 45, 'y': 67}
        """
        pointlist = self.get_pointlist()
        for i in range(len(pointlist)):
            pointlist[i] = sorted(pointlist[i], key=lambda p: p["time"])
        pointlist = sorted(pointlist, key=lambda stroke: stroke[0]["time"])
        return pointlist

    def set_pointlist(self, pointlist):
        """Overwrite pointlist.

        Parameters
        ----------
        pointlist : a list of strokes; each stroke is a list of points
            The inner lists represent strokes. Every stroke consists of points.
            Every point is a dictinary with 'x', 'y', 'time'.
        """
        assert type(pointlist) is list, "pointlist is not of type list, but %r" % type(
            pointlist
        )
        assert len(pointlist) >= 1, "The pointlist of formula_id %i is %s" % (
            self.formula_id,
            self.get_pointlist(),
        )
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
        return {
            "minx": minx,
            "maxx": maxx,
            "miny": miny,
            "maxy": maxy,
            "mint": mint,
            "maxt": maxt,
        }

    def get_width(self):
        """Get the width of the rectangular, axis-parallel bounding box."""
        box = self.get_bounding_box()
        return box["maxx"] - box["minx"]

    def get_height(self):
        """Get the height of the rectangular, axis-parallel bounding box."""
        box = self.get_bounding_box()
        return box["maxy"] - box["miny"]

    def get_area(self):
        """Get the area in square pixels of the recording."""
        return (self.get_height() + 1) * (self.get_width() + 1)

    def get_time(self):
        """Get the time in which the recording was created."""
        box = self.get_bounding_box()
        return box["maxt"] - box["mint"]

    def get_bitmap(self, time=None, size=32, store_path=None):
        """
        Get a bitmap of the object at a given instance of time. If time is
        `None`,`then the bitmap is generated for the last point in time.

        Parameters
        ----------
        time : int or None
        size : int
            Size in pixels. The resulting bitmap will be (size x size).
        store_path : None or str
            If this is set, then the image will be saved there.

        Returns
        -------
        numpy array :
            Greyscale png image
        """
        # bitmap_width = int(self.get_width()*size) + 2
        # bitmap_height = int(self.get_height()*size) + 2
        img = Image.new("L", (size, size), "black")
        draw = ImageDraw.Draw(img, "L")
        bb = self.get_bounding_box()
        for stroke in self.get_sorted_pointlist():
            for p1, p2 in zip(stroke, stroke[1:]):
                if time is not None and (p1["time"] > time or p2["time"] > time):
                    continue
                y_from = int((-bb["miny"] + p1["y"]) / max(self.get_height(), 1) * size)
                x_from = int((-bb["minx"] + p1["x"]) / max(self.get_width(), 1) * size)
                y_to = int((-bb["miny"] + p2["y"]) / max(self.get_height(), 1) * size)
                x_to = int((-bb["minx"] + p2["x"]) / max(self.get_width(), 1) * size)
                draw.line([x_from, y_from, x_to, y_to], fill="#ffffff", width=1)
        del draw
        if store_path is not None:
            img.save(store_path)
        return numpy.asarray(img)

    def preprocessing(self, algorithms: List[Callable]):
        """Apply preprocessing algorithms.

        Parameters
        ----------
        algorithms : a list objects
            Preprocessing allgorithms which get applied in order.

        Examples
        --------
        >>> from hwrt import preprocessing
        >>> a = HandwrittenData.generate()
        >>> preprocessing_queue = [preprocessing.ScaleAndShift(),
        ...                        preprocessing.StrokeConnect(),
        ...                        preprocessing.DouglasPeucker(epsilon=0.2),
        ...                        preprocessing.SpaceEvenly(number=100,
        ...                         kind='cubic')]
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
            assert len(new_features) == algorithm.get_dimension(), (
                "Expected %i features from algorithm %s, got %i features"
                % (algorithm.get_dimension(), str(algorithm), len(new_features))
            )
            features += new_features
        return features

    def show(self):
        """Show the data graphically in a new pop-up window."""
        import matplotlib.pyplot as plt

        pointlist = self.get_pointlist()
        if "pen_down" in pointlist[0][0]:
            assert len(pointlist) > 1, "Lenght of pointlist was %i. Got: %s" % (
                len(pointlist),
                pointlist,
            )
            # Create a new pointlist that models pen-down strokes and pen
            # up strokes
            new_pointlist = []
            last_pendown_state = None
            stroke = []
            for point in pointlist[0]:
                if last_pendown_state is None:
                    last_pendown_state = point["pen_down"]
                if point["pen_down"] != last_pendown_state:
                    new_pointlist.append(stroke)
                    last_pendown_state = point["pen_down"]
                    stroke = []
                else:
                    stroke.append(point)
            new_pointlist.append(stroke)  # add the last stroke
            pointlist = new_pointlist

        _, ax = plt.subplots()
        ax.set_title(
            "Raw data id: %s, "
            "Formula_id: %s" % (str(self.raw_data_id), str(self.formula_id))
        )

        colors = _get_colors(self.segmentation)
        for symbols, color in zip(self.segmentation, colors):
            for stroke_index in symbols:
                stroke = pointlist[stroke_index]
                xs, ys = [], []
                for p in stroke:
                    xs.append(p["x"])
                    ys.append(p["y"])
                if "pen_down" in stroke[0] and stroke[0]["pen_down"] is False:
                    plt.plot(xs, ys, "-x", color=color)
                else:
                    plt.plot(xs, ys, "-o", color=color)
        plt.gca().invert_yaxis()
        ax.set_aspect("equal")
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
        xsum, ysum, counter = 0.0, 0.0, 0
        for stroke in self.get_pointlist():
            for point in stroke:
                xsum += point["x"]
                ysum += point["y"]
                counter += 1
        return (xsum / counter, ysum / counter)

    def to_single_symbol_list(self):
        """
        Convert this HandwrittenData object into a list of HandwrittenData
        objects. Each element of the list is a single symbol.

        Returns
        -------
        list of HandwrittenData objects
        """
        symbol_stream = getattr(
            self, "symbol_stream", [None for symbol in self.segmentation]
        )
        single_symbols = []
        pointlist = self.get_sorted_pointlist()
        for stroke_indices, label in zip(self.segmentation, symbol_stream):
            strokes = []
            for stroke_index in stroke_indices:
                strokes.append(pointlist[stroke_index])
            single_symbols.append(
                HandwrittenData(json.dumps(strokes), formula_id=label)
            )
        return single_symbols

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        if self.raw_data_id is None and self.formula_in_latex is not None:
            return "HandwrittenData(%s)" % str(self.formula_in_latex)
        else:
            return "HandwrittenData(raw_data_id=%s)" % str(self.raw_data_id)

    def __str__(self):
        return repr(self)


def _get_colors(segmentation):
    """Get a list of colors which is as long as the segmentation.

    Parameters
    ----------
    segmentation : list of lists

    Returns
    -------
    list
        A list of colors.
    """
    symbol_count = len(segmentation)
    num_colors = symbol_count

    # See http://stackoverflow.com/a/20298116/562769
    color_array = [
        "#000000",
        "#FFFF00",
        "#1CE6FF",
        "#FF34FF",
        "#FF4A46",
        "#008941",
        "#006FA6",
        "#A30059",
        "#FFDBE5",
        "#7A4900",
        "#0000A6",
        "#63FFAC",
        "#B79762",
        "#004D43",
        "#8FB0FF",
        "#997D87",
        "#5A0007",
        "#809693",
        "#FEFFE6",
        "#1B4400",
        "#4FC601",
        "#3B5DFF",
        "#4A3B53",
        "#FF2F80",
        "#61615A",
        "#BA0900",
        "#6B7900",
        "#00C2A0",
        "#FFAA92",
        "#FF90C9",
        "#B903AA",
        "#D16100",
        "#DDEFFF",
        "#000035",
        "#7B4F4B",
        "#A1C299",
        "#300018",
        "#0AA6D8",
        "#013349",
        "#00846F",
        "#372101",
        "#FFB500",
        "#C2FFED",
        "#A079BF",
        "#CC0744",
        "#C0B9B2",
        "#C2FF99",
        "#001E09",
        "#00489C",
        "#6F0062",
        "#0CBD66",
        "#EEC3FF",
        "#456D75",
        "#B77B68",
        "#7A87A1",
        "#788D66",
        "#885578",
        "#FAD09F",
        "#FF8A9A",
        "#D157A0",
        "#BEC459",
        "#456648",
        "#0086ED",
        "#886F4C",
        "#34362D",
        "#B4A8BD",
        "#00A6AA",
        "#452C2C",
        "#636375",
        "#A3C8C9",
        "#FF913F",
        "#938A81",
        "#575329",
        "#00FECF",
        "#B05B6F",
        "#8CD0FF",
        "#3B9700",
        "#04F757",
        "#C8A1A1",
        "#1E6E00",
        "#7900D7",
        "#A77500",
        "#6367A9",
        "#A05837",
        "#6B002C",
        "#772600",
        "#D790FF",
        "#9B9700",
        "#549E79",
        "#FFF69F",
        "#201625",
        "#72418F",
        "#BC23FF",
        "#99ADC0",
        "#3A2465",
        "#922329",
        "#5B4534",
        "#FDE8DC",
        "#404E55",
        "#0089A3",
        "#CB7E98",
        "#A4E804",
        "#324E72",
        "#6A3A4C",
        "#83AB58",
        "#001C1E",
        "#D1F7CE",
        "#004B28",
        "#C8D0F6",
        "#A3A489",
        "#806C66",
        "#222800",
        "#BF5650",
        "#E83000",
        "#66796D",
        "#DA007C",
        "#FF1A59",
        "#8ADBB4",
        "#1E0200",
        "#5B4E51",
        "#C895C5",
        "#320033",
        "#FF6832",
        "#66E1D3",
        "#CFCDAC",
        "#D0AC94",
        "#7ED379",
        "#012C58",
    ]

    # Apply a little trick to make sure we have enough colors, no matter
    # how many symbols are in one recording.
    # This simply appends the color array as long as necessary to get enough
    # colors
    new_array = color_array[:]
    while len(new_array) <= num_colors:
        new_array += color_array

    return new_array[:num_colors]
