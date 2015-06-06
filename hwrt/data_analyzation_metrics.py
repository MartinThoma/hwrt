#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Data analyzation metrics

Each algorithm works on a set of handwritings. They have to be applied like
this:

>>> import data_analyzation_metrics
>>> a = [{'is_in_testset': 0,
...    'formula_id': 31L,
...    'handwriting': HandwrittenData(raw_data_id=2953),
...    'formula_in_latex': 'A',
...    'id': 2953L},
...   {'is_in_testset': 0,
...    'formula_id': 31L,
...    'handwriting': HandwrittenData(raw_data_id=4037),
...    'formula_in_latex': 'A',
...    'id': 4037L},
...   {'is_in_testset': 0,
...    'formula_id': 31L,
...    'handwriting': HandwrittenData(raw_data_id=4056),
...    'formula_in_latex': 'A',
...    'id': 4056L}]
>>> creator_metric = Creator('creator.csv')
>>> creator_metric(a)
"""
from __future__ import print_function
import os
import logging
import sys
import time
from collections import defaultdict
import math
import numpy

# hwrt modules
# HandwrittenData and preprocessing are needed because of pickle
from . import HandwrittenData  # pylint: disable=W0611
from . import preprocessing  # pylint: disable=W0611
from . import utils


def get_metrics(metrics_description):
    """Get metrics from a list of dictionaries. """
    return utils.get_objectlist(metrics_description,
                                config_key='data_analyzation_plugins',
                                module=sys.modules[__name__])

# Helper functions that are useful for some metrics


def prepare_file(filename):
    """Truncate the file and return the filename."""
    directory = os.path.join(utils.get_project_root(), "analyzation/")
    if not os.path.exists(directory):
        os.makedirs(directory)
    workfilename = os.path.join(directory, filename)
    open(workfilename, 'w').close()  # Truncate the file
    return workfilename


def sort_by_formula_id(raw_datasets):
    """
    Sort a list of formulas by `id`, where `id` represents the accepted
    formula id.

    Parameters
    ----------
    raw_datasets : list of dictionaries
        A list of raw datasets.

    Examples
    --------
    The parameter `raw_datasets` has to be of the format

    >>> rd = [{'is_in_testset': 0,
    ...        'formula_id': 31,
    ...        'handwriting': HandwrittenData(raw_data_id=2953),
    ...        'formula_in_latex': 'A',
    ...        'id': 2953},
    ...       {'is_in_testset': 0,
    ...        'formula_id': 31,
    ...        'handwriting': HandwrittenData(raw_data_id=4037),
    ...        'formula_in_latex': 'A',
    ...        'id': 4037},
    ...       {'is_in_testset': 0,
    ...        'formula_id': 31,
    ...        'handwriting': HandwrittenData(raw_data_id=4056),
    ...        'formula_in_latex': 'A',
    ...        'id': 4056}]
    >>> sort_by_formula_id(rd)
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
        write_file.write("creatorid,nr of recordings\n")  # heading

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
                point1 = last_stroke[-1]
                point2 = stroke[0]
                space_dist = math.hypot(point1['x'] - point2['x'],
                                        point1['y'] - point2['y'])
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
        return "TimeBetweenPointsAndStrokes(%s, %s)" % \
            (self.filename_points, self.filename_strokes)

    def __str__(self):
        return "TimeBetweenPointsAndStrokes(%s, %s)" % \
            (self.filename_points, self.filename_strokes)

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
            for stroke in raw_dataset['handwriting'].get_sorted_pointlist():
                if last_stroke_end is not None:
                    times_between_strokes.append(stroke[-1]['time'] -
                                                 last_stroke_end)
                last_stroke_end = stroke[-1]['time']
                for point1, point2 in zip(stroke, stroke[1:]):
                    delta = point2['time'] - point1['time']
                    times_between_points.append(delta)
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


class AnalyzeErrors(object):
    """Analyze the number of errors in the dataset."""

    def __init__(self, filename="errors.txt", time_max_threshold=30*1000):
        self.filename = prepare_file(filename)
        self.time_max_threshold = time_max_threshold  # in ms
        self.dot_symbols = ['i', 'j', '\cdot', '\div', '\\because',
                            '\\therefore']  # TODO: Use the tags!

    def __repr__(self):
        return "AnalyzeErrors"

    def __str__(self):
        return "AnalyzeErrors"

    def _write_data(self, symbols, err_recs, nr_recordings,
                    total_error_count, percentages, time_max_list):
        """Write all obtained data to a file.

        Parameters
        ----------
        symbols : list of tuples (String, non-negative int)
            List of all symbols with the count of recordings
        err_recs : dictionary
            count of recordings by error type
        nr_recordings : non-negative int
            number of recordings
        total_error_count : dictionary
            Count of all error that have happened by type
        percentages : list
            List of all recordings where removing the dots changed the size of
            the bounding box.
        time_max_list : list
            List of all recordings where the recording time is above a
            threshold.
        """
        write_file = open(self.filename, "a")
        s = ""
        for symbol, count in sorted(symbols.items(), key=lambda n: n[0]):
            if symbol in ['a', '0', 'A']:
                s += "\n%s (%i), " % (symbol, count)
            elif symbol in ['z', '9', 'Z']:
                s += "%s (%i) \n" % (symbol, count)
            else:
                s += "%s (%i), " % (symbol, count)
        print("## Data", file=write_file)
        print("Symbols: %i" % len(symbols), file=write_file)
        print("Recordings: %i" % sum(symbols.values()), file=write_file)
        print("```", file=write_file)
        print(s[:-1], file=write_file)
        print("```", file=write_file)

        # Show errors
        print("Recordings with wild points: %i (%0.2f%%)" %
              (err_recs['wild_points'],
               float(err_recs['wild_points'])/nr_recordings*100),
              file=write_file)
        print("wild points: %i" % total_error_count['wild_points'],
              file=write_file)
        print("Recordings with missing stroke: %i (%0.2f%%)" %
              (err_recs['missing_stroke'],
               float(err_recs['missing_stroke'])/nr_recordings*100),
              file=write_file)
        print("Recordings with errors: %i (%0.2f%%)" %
              (err_recs['total'],
               float(err_recs['total'])/nr_recordings*100),
              file=write_file)
        print("Recordings with dots: %i (%0.2f%%)" %
              (err_recs['single_dots'],
               float(err_recs['single_dots'])/nr_recordings*100),
              file=write_file)
        print("dots: %i" % total_error_count['single_dots'], file=write_file)
        print("size changing removal: %i (%0.2f%%)" %
              (len(percentages),
               float(len(percentages))/nr_recordings*100),
              file=write_file)
        print("%i recordings took more than %i ms. That were: " %
              (len(time_max_list), self.time_max_threshold),
              file=write_file)
        for recording in time_max_list:
            print("* %ims: %s: %s" %
                  (recording.get_time(),
                   utils.get_readable_time(recording.get_time()),
                   recording),
                  file=write_file)
        write_file.close()

    def __call__(self, raw_datasets):
        # Initialize variables
        symbols = defaultdict(int)

        # Count errornous recordings
        err_recs = {'wild_points': 0, 'missing_stroke': 0,
                    'single_dots': 0,  # except symbols_with_dots
                    'total': 0}

        # Count errors (one type of error might occur multiple times in
        # a single recording)
        total_error_count = {'wild_points': 0, 'single_dots': 0}

        percentages = []

        # List with recordings that are over the time maximum
        time_max_list = []

        for raw_dataset in raw_datasets:
            recording = raw_dataset['handwriting']
            symbols[recording.formula_in_latex] += 1
            if recording.get_time() > self.time_max_threshold:
                time_max_list.append(recording)
            if recording.wild_point_count > 0:
                err_recs['wild_points'] += 1
                total_error_count['wild_points'] += recording.wild_point_count
            err_recs['missing_stroke'] += recording.missing_stroke
            if recording.wild_point_count > 0 or \
               recording.missing_stroke:
                err_recs['total'] += 1
            if recording.count_single_dots() > 0 and \
               raw_dataset['formula_in_latex'] not in self.dot_symbols and \
               "dots" not in raw_dataset['formula_in_latex']:
                err_recs['single_dots'] += 1
                old_area = recording.get_area()
                tmp = [preprocessing.RemoveDots()]
                recording.preprocessing(tmp)
                new_area = recording.get_area()
                percentage = float(new_area)/float(old_area)
                if percentage < 1.0:
                    percentages.append(percentage)
            total_error_count['single_dots'] += recording.count_single_dots()

        time_max_list = sorted(time_max_list,
                               key=lambda n: n.get_time(),
                               reverse=True)

        self._write_data(symbols, err_recs, len(raw_datasets),
                         total_error_count, percentages,
                         time_max_list)
