#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Data analyzation metrics

Each algorithm works on a set of handwritings. They have to be applied like
this:

 >>> import data_analyzation_metrics
 >>> a = [{'is_in_testset': 0,
           'formula_id': 31L,
           'handwriting': HandwrittenData(raw_data_id=2953),
           'formula_in_latex': 'A',
           'id': 2953L},
          {'is_in_testset': 0,
           'formula_id': 31L,
           'handwriting': HandwrittenData(raw_data_id=4037),
           'formula_in_latex': 'A',
           'id': 4037L},
          {'is_in_testset': 0,
           'formula_id': 31L,
           'handwriting': HandwrittenData(raw_data_id=4056),
           'formula_in_latex': 'A',
           'id': 4056L}]
 >>> creator_metric = Creator('creator.csv')
 >>> creator_metric(a)
"""
import inspect
import imp
import os
import logging
import sys
import time
from collections import defaultdict
import math
import numpy

# hwrt modules
from . import HandwrittenData  # Necessary for pickle files
from . import preprocessing  # Necessary for pickle files
from . import utils


def get_class(name):
    """Get the class by its name as a string."""
    clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    for string_name, act_class in clsmembers:
        if string_name == name:
            return act_class

    # Check if the user has specified a plugin and if the class is in there
    cfg = utils.get_project_configuration()
    if 'data_analyzation_plugins' in cfg:
        basename = os.path.basename(cfg['data_analyzation_plugins'])
        modname = os.path.splitext(basename)[0]
        if os.path.isfile(cfg['data_analyzation_plugins']):
            usermodule = imp.load_source(modname,
                                         cfg['data_analyzation_plugins'])
            clsmembers = inspect.getmembers(usermodule, inspect.isclass)
            for string_name, act_class in clsmembers:
                if string_name == name:
                    return act_class
        else:
            logging.warning("File '%s' does not exist. Adjust ~/.hwrtrc.",
                            cfg['data_analyzation_plugins'])

    logging.warning("Unknown class '%s'.", name)
    return None


def get_metrics(metrics_description):
    """Get metrics from a list of dictionaries. """
    metric_list = []
    for metric in metrics_description:
        for feat, params in metric.items():
            feat = get_class(feat)
            if feat is not None:
                if params is None:
                    metric_list.append(feat())
                else:
                    parameters = {}
                    for dicts in params:
                        for param_name, param_value in dicts.items():
                            parameters[param_name] = param_value
                    metric_list.append(feat(**parameters))
    return metric_list

# Helper functions that are useful for some metrics


def prepare_file(filename):
    """Trunkate the file and return the filename."""
    root = utils.get_project_root()
    directory = os.path.join(root, "analyzation/")
    if not os.path.exists(directory):
        os.makedirs(directory)
    workfilename = os.path.join(directory, filename)
    open(workfilename, 'w').close()  # Truncate the file
    return workfilename


def sort_by_formula_id(raw_datasets):
    """The parameter ``raw_datasets`` has to be of the format

        [{'is_in_testset': 0,
          'formula_id': 31L,
          'handwriting': HandwrittenData(raw_data_id=2953),
          'formula_in_latex': 'A',
          'id': 2953L},
         {'is_in_testset': 0,
          'formula_id': 31L,
          'handwriting': HandwrittenData(raw_data_id=4037),
          'formula_in_latex': 'A',
          'id': 4037L},
         {'is_in_testset': 0,
          'formula_id': 31L,
          'handwriting': HandwrittenData(raw_data_id=4056),
          'formula_in_latex': 'A',
          'id': 4056L}]
    """
    by_formula_id = defaultdict(list)
    for el in raw_datasets:
        by_formula_id[el['handwriting'].formula_id].append(el['handwriting'])
    return by_formula_id


# Only data analyzation calculation classes follow
# Every class must have a __str__, __repr__ and __call__ function where
# __call__ must take exactly one argument of type list of dictionaries
# Every class must have a constructor which takes the filename as a parameter.
# This filename has to be used to write the evaluation results
# (preferably in CSV format) to this file.
# prepare_file should be applied to every file in the constructor


class Creator(object):
    """Analyze who created most of the data."""

    def __init__(self, filename="creator.csv"):
        self.filename = prepare_file(filename)

    def __repr__(self):
        return "AnalyzeCreator(%s)" % self.filename

    def __str__(self):
        return "AnalyzeCreator(%s)" % self.filename

    def __call__(self, raw_datasets):
        write_file = open(self.filename, "a")
        write_file.write("creatorid,nr of symbols\n")  # heading

        print_data = defaultdict(int)
        start_time = time.time()
        for i, raw_dataset in enumerate(raw_datasets):
            if i % 100 == 0 and i > 0:
                utils.print_status(len(raw_datasets), i, start_time)
            print_data[raw_dataset['handwriting'].user_id] += 1
        print("\r100%"+"\033[K\n")

        # Sort the data by highest value, descending
        print_data = sorted(print_data.items(),
                            key=lambda n: n[1],
                            reverse=True)

        # Write data to file
        write_file.write("total,%i\n" %
                         sum([value for _, value in print_data]))
        for userid, value in print_data:
            write_file.write("%s,%i\n" % (str(userid), value))
        write_file.close()


class InstrokeSpeed(object):
    """Analyze how fast the points were in pixel/ms."""

    def __init__(self, filename="instroke_speed.csv"):
        self.filename = prepare_file(filename)

    def __repr__(self):
        return "InstrokeSpeed(%s)" % self.filename

    def __str__(self):
        return "InstrokeSpeed(%s)" % self.filename

    def __call__(self, raw_datasets):
        write_file = open(self.filename, "a")
        write_file.write("speed\n")  # heading

        print_data = []
        start_time = time.time()
        for i, raw_dataset in enumerate(raw_datasets):
            if i % 100 == 0 and i > 0:
                utils.print_status(len(raw_datasets), i, start_time)
            pointlist = raw_dataset['handwriting'].get_sorted_pointlist()

            for stroke in pointlist:
                for last_point, point in zip(stroke, stroke[1:]):
                    space_dist = math.hypot(last_point['x'] - point['x'],
                                            last_point['y'] - point['y'])
                    time_delta = point['time'] - last_point['time']
                    if time_delta == 0:
                        continue
                    print_data.append(space_dist/time_delta)
        print("\r100%"+"\033[K\n")
        # Sort the data by highest value, descending
        print_data = sorted(print_data, reverse=True)
        # Write data to file
        for value in print_data:
            write_file.write("%0.8f\n" % (value))

        logging.info("instroke speed mean: %0.8f", numpy.mean(print_data))
        logging.info("instroke speed std: %0.8f", numpy.std(print_data))
        write_file.close()


class InterStrokeDistance(object):
    """Analyze how much distance in px is between strokes."""

    def __init__(self, filename="dist_between_strokes.csv"):
        self.filename = prepare_file(filename)

    def __repr__(self):
        return "InterStrokeDistance(%s)" % self.filename

    def __str__(self):
        return "InterStrokeDistance(%s)" % self.filename

    def __call__(self, raw_datasets):
        write_file = open(self.filename, "a")
        write_file.write("speed\n")  # heading

        print_data = []
        start_time = time.time()
        for i, raw_dataset in enumerate(raw_datasets):
            if i % 100 == 0 and i > 0:
                utils.print_status(len(raw_datasets), i, start_time)
            pointlist = raw_dataset['handwriting'].get_sorted_pointlist()

            for last_stroke, stroke in zip(pointlist, pointlist[1:]):
                p1 = last_stroke[-1]
                p2 = stroke[0]
                space_dist = math.hypot(p1['x'] - p2['x'],
                                        p1['y'] - p2['y'])
                print_data.append(space_dist)
        print("\r100%"+"\033[K\n")
        # Sort the data by highest value, descending
        print_data = sorted(print_data, reverse=True)
        # Write data to file
        for value in print_data:
            write_file.write("%0.8f\n" % (value))

        logging.info("dist_between_strokes mean:\t%0.8fpx",
                     numpy.mean(print_data))
        logging.info("dist_between_strokes std: \t%0.8fpx",
                     numpy.std(print_data))
        write_file.close()


class TimeBetweenPointsAndStrokes(object):
    """For each recording: Store the average time between controll points of
       one stroke / controll points of two different strokes.
    """

    def __init__(self, filename="average_time_between_points.txt",
                 filename_strokes="average_time_between_strokes.txt"):
        self.filename_points = prepare_file(filename)
        self.filename_strokes = prepare_file(filename_strokes)

    def __repr__(self):
        return "TimeBetweenPointsAndStrokes(%s)" % self.filename

    def __str__(self):
        return "TimeBetweenPointsAndStrokes(%s)" % self.filename

    def __call__(self, raw_datasets):
        average_between_points = open(self.filename_points, "a")
        average_between_strokes = open(self.filename_strokes, "a")
        start_time = time.time()
        for i, raw_dataset in enumerate(raw_datasets):
            if i % 100 == 0 and i > 0:
                utils.print_status(len(raw_datasets), i, start_time)

            # Do the work
            times_between_points, times_between_strokes = [], []
            last_stroke_end = None
            if len(raw_dataset['handwriting'].get_pointlist()) == 0:
                logging.warning("%i has no content.",
                                raw_dataset['handwriting'].raw_data_id)
                continue
            for stroke in raw_dataset['handwriting'].get_sorted_pointlist():
                if last_stroke_end is not None:
                    times_between_strokes.append(stroke[-1]['time'] -
                                                 last_stroke_end)
                last_stroke_end = stroke[-1]['time']
                last_point_end = None
                for point in stroke:
                    if last_point_end is not None:
                        times_between_points.append(point['time'] -
                                                    last_point_end)
                    last_point_end = point['time']
            # The recording might only have one point
            if len(times_between_points) > 0:
                tmp = times_between_points
                average_between_points.write("%0.2f\n" % numpy.average(tmp))
            # The recording might only have one stroke
            if len(times_between_strokes) > 0:
                tmp = times_between_strokes
                average_between_strokes.write("%0.2f\n" % numpy.average(tmp))
        print("\r100%"+"\033[K\n")
        average_between_points.close()
        average_between_strokes.close()
