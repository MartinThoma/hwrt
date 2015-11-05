#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Get a set of features for WILDPOINT detection for a list of handwritings."""

import yaml
import os
import pickle

from hwrt import preprocessing


def main():
    tarfolder = "/home/moose/GitHub/hwrt/hwrt/wildpoints/"
    recordings = get_recordings(tarfolder)
    preprocess(tarfolder, recordings)
    Xs, ys = get_features(recordings)


def get_recordings(tarfolder):
    picklefile = os.path.join(tarfolder, "wildpoint-data-old.pickle")
    with open(picklefile, "rb") as handle:
        recordings = pickle.load(handle)
    return recordings


def preprocess(tarfolder, recordings):
    # Get the preprocessing
    with open(os.path.join(tarfolder, "preprocessing.yml"), 'r') as ymlfile:
        preprocessing_description = yaml.load(ymlfile)
    preprocessing_queue = preprocessing.get_preprocessing_queue(
        preprocessing_description['queue'])
    for recording in recordings:
        recording.preprocessing(preprocessing_queue)


def get_features(recordings):
    """
    Parameters
    ----------
    recordings : list of HandwrittenData objects

    Returns
    -------
    tuple (Xs, ys)
        Xs and ys are lists of the same length. Each element of Xs is a list of
        float values, each element of ys is a list of 0s and 1s. A 1 means the
        features represented at the same index in Xs belong to a WILDPOINT, a
        0 means the features represented at the same index in Xs belongs not to
        a WILDPOINT
    """
    Xs, ys = [], []
    for hw in recordings:
        zipped = zip(hw.get_sorted_pointlist(),
                     hw.ann_segmentation['symbol-ids'])
        for stroke, symbol_id in zipped:
            X = get_stroke_features(stroke)
            Xs.append(X)
            ys.append(symbol_id == 3992)
    return (Xs, ys)


def get_stroke_features(stroke):
    """
    Parameters
    ----------
    stroke : 
    """
    pass

if __name__ == '__main__':
    main()
