#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Segmentation is the task of splitting a data sequence into chuncks which can
then be classified chunk by chunk.

In the case of handwritten formula recognition it might be ok to segment by
strokes. However, one should note that cursive handwriting might make it
necessary to split on the point level.

Segmenting in the order in which strokes were written is also problematic as
delayed strokes (e.g. for extending a fraction stroke which was too short)
might occur.

This module contains algorithms for segmentation.
"""

import logging
import json

import itertools
import numpy
import os

import pickle

# hwrt modules
# from . import HandwrittenData
from hwrt import utils
from hwrt.HandwrittenData import HandwrittenData
from hwrt import features
from hwrt import geometry

stroke_segmented_classifier = None


def _get_symbol_index(stroke_id_needle, segmentation):
    """
    :returns: The symbol index in which stroke_id_needle occurs

    >>> _get_symbol_index(3, [[0, 1, 2], [3, 4, 5], [6, 7]])
    1
    >>> _get_symbol_index(6, [[0, 1, 2], [3, 4, 5], [6, 7]])
    2
    >>> _get_symbol_index(7, [[0, 1, 2], [3, 4, 5], [6, 7]])
    2
    """
    for symbol_index, symbol in enumerate(segmentation):
        if stroke_id_needle in symbol:
            return symbol_index
    return None


def get_segmented_raw_data():
    import pymysql.cursors
    cfg = utils.get_database_configuration()
    mysql = cfg['mysql_dev']
    connection = pymysql.connect(host=mysql['host'],
                                 user=mysql['user'],
                                 passwd=mysql['passwd'],
                                 db=mysql['db'],
                                 cursorclass=pymysql.cursors.DictCursor)
    cursor = connection.cursor()
    sql = ("SELECT `id`, `data`, `segmentation` "
           "FROM `wm_raw_draw_data` WHERE `segmentation` "
           "IS NOT NULL AND `wild_point_count` = 0 "
           "ORDER BY `id` LIMIT 0, 4000")
    cursor.execute(sql)
    datasets = cursor.fetchall()
    return datasets


def get_dataset():
    """Create a dataset for machine learning.

    :returns: (X, y) where X is a list of tuples. Each tuple is a feature. y
              is a list of labels
              (0 for 'not in one symbol' and 1 for 'in symbol')
    """
    seg_data = "segmentation-X.npy"
    seg_labels = "segmentation-y.npy"
    if os.path.isfile(seg_data) and os.path.isfile(seg_labels):
        X = numpy.load(seg_data)
        y = numpy.load(seg_labels)
        with open('datasets.pickle', 'rb') as f:
            datasets = pickle.load(f)
        return (X, y, datasets)
    datasets = get_segmented_raw_data()
    X, y = [], []
    for i, data in enumerate(datasets):
        if i % 10 == 0:
            logging.info("i=%i", i)
        # logging.info("Start looking at dataset %i", i)
        segmentation = json.loads(data['segmentation'])
        # logging.info(segmentation)
        recording = json.loads(data['data'])
        X_symbol = [get_median_stroke_distance(recording)]
        if len([p for s in recording for p in s if p['time'] is None]) > 0:
            continue
        for strokeid1, strokeid2 in itertools.combinations(list(range(len(recording))), 2):
            stroke1 = recording[strokeid1]
            stroke2 = recording[strokeid2]
            if len(stroke1) == 0 or len(stroke2) == 0:
                logging.debug("stroke len 0. Skip.")
                continue
            X.append(get_stroke_features(recording, strokeid1, strokeid2)+X_symbol)
            same_symbol = (_get_symbol_index(strokeid1, segmentation) ==
                           _get_symbol_index(strokeid2, segmentation))
            y.append(int(same_symbol))
    X = numpy.array(X, dtype=numpy.float32)
    y = numpy.array(y, dtype=numpy.int32)
    numpy.save(seg_data, X)
    numpy.save(seg_labels, y)
    with open('datasets.pickle', 'wb') as f:
        pickle.dump(datasets, f, protocol=pickle.HIGHEST_PROTOCOL)
    return (X, y, datasets)


def get_nn_classifier(X, y):
    import lasagne
    import theano
    import theano.tensor as T
    N_CLASSES = 2

    # First, construct an input layer.
    # The shape parameter defines the expected input shape, which is just the shape of our data matrix X.
    l_in = lasagne.layers.InputLayer(shape=X.shape)
    # A dense layer implements a linear mix (xW + b) followed by a nonlinearity.
    hiddens = [64, 64, 64]  # sollte besser als 0.12 sein (mit [32])
    layers = [l_in]

    for n_units in hiddens:
        l_hidden_1 = lasagne.layers.DenseLayer(
            layers[-1],  # The first argument is the input to this layer
            num_units=n_units,  # This defines the layer's output dimensionality
            nonlinearity=lasagne.nonlinearities.tanh)  # Various nonlinearities are available such as relu
        layers.append(l_hidden_1)
    # For our output layer, we'll use a dense layer with a softmax nonlinearity.
    l_output = lasagne.layers.DenseLayer(layers[-1], num_units=N_CLASSES,
                                         nonlinearity=lasagne.nonlinearities.softmax)
    # Now, we can generate the symbolic expression of the network's output given an input variable.
    net_input = T.matrix('net_input')
    net_output = l_output.get_output(net_input)
    # As a loss function, we'll use Theano's categorical_crossentropy function.
    # This allows for the network output to be class probabilities,
    # but the target output to be class labels.
    true_output = T.ivector('true_output')
    loss = T.mean(T.nnet.categorical_crossentropy(net_output, true_output))

    reg = lasagne.regularization.l2(l_output)
    loss = loss + 0.001*reg
    #NLL_LOSS = -T.sum(T.log(p_y_given_x)[T.arange(y.shape[0]), y])
    # Retrieving all parameters of the network is done using get_all_params,
    # which recursively collects the parameters of all layers connected to the provided layer.
    all_params = lasagne.layers.get_all_params(l_output)

    # Now, we'll generate updates using Lasagne's SGD function
    updates = lasagne.updates.momentum(loss, all_params, learning_rate=0.1)

    # Finally, we can compile Theano functions for training and computing the output.
    train = theano.function([net_input, true_output], loss, updates=updates)
    get_output = theano.function([net_input], net_output)

    #from sklearn.preprocessing import StandardScaler
    #scaler = StandardScaler()
    #X_train_s = scaler.fit_transform(X_train)
    #X_test_s = scaler.transform(X_test)

    logging.debug("|X|=%i", len(X))
    logging.debug("|y|=%i", len(y))
    logging.debug("|X[0]|=%i", len(X[0]))

    # Train
    epochs = 20
    for n in range(epochs):
        train(X, y)
    return get_output


def get_stroke_features(recording, strokeid1, strokeid2):
    """Get the features used to decide if two strokes belong to the same symbol
    or not.

    * Distance of bounding boxes
    """
    stroke1 = recording[strokeid1]
    stroke2 = recording[strokeid2]
    assert isinstance(stroke1, list), "stroke1 is a %s" % type(stroke1)
    X_i = []
    for s in [stroke1, stroke2]:
        hw = HandwrittenData(json.dumps([s]))
        feat1 = features.ConstantPointCoordinates(strokes=1,
                                                  points_per_stroke=20,
                                                  fill_empty_with=0)
        feat2 = features.ReCurvature(strokes=1)
        feat3 = features.Ink()
        X_i += hw.feature_extraction([feat1, feat2, feat3])
    X_i += [get_strokes_distance(stroke1, stroke2)]  # Distance of strokes
    X_i += [get_time_distance(stroke1, stroke2)]  # Time in between
    X_i += [abs(strokeid2-strokeid1)]  # Strokes in between
    return X_i


def get_median_stroke_distance(recording):
    dists = []
    for s1_id in range(len(recording)-1):
        for s2_id in range(s1_id+1, len(recording)):
            dists.append(get_strokes_distance(recording[s1_id],
                                              recording[s2_id]))
    return numpy.median(dists)


def get_time_distance(s1, s2):
    min_dist = abs(s1[0]['time'] - s2[0]['time'])
    for p1, p2 in zip(s1, s2):
        dist = abs(p1['time'] - p2['time'])
        min_dist = min(min_dist, dist)
    return min_dist


def get_strokes_distance(s1, s2):
    if len(s1) == 1:
        s1 += s1
    if len(s2) == 1:
        s2 += s2
    stroke1 = geometry.PolygonalChain(s1)
    stroke2 = geometry.PolygonalChain(s2)
    import itertools
    min_dist = geometry.segments_distance(stroke1[0], stroke2[0])
    for seg1, seg2 in itertools.product(stroke1, stroke2):
        min_dist = min(min_dist, geometry.segments_distance(seg1, seg2))
    return min_dist


def get_segmentation(recording):
    """
    :param recording: A list of lists, where each sublist represents a stroke
    :returns: A list of segmentations together with their probabilities. Each
              probability has to be positive and the sum may not be bigger than
              1.0.

    >> segment([stroke1, stroke2, stroke3])
    [
      ([[0, 1], [2]], 0.8),
      ([[0], [1,2]], 0.1),
      ([[0,2], [1]], 0.05)
    ]
    """
    global stroke_segmented_classifier
    X_symbol = [get_median_stroke_distance(recording)]
    if stroke_segmented_classifier is None:
        logging.info("Start creation of training set")
        X, y, datasets = get_dataset()
        logging.info("Start training")
        nn = get_nn_classifier(X, y)
        stroke_segmented_classifier = lambda X: nn(X)[0][1]
        #import pprint
        #pp = pprint.PrettyPrinter(indent=4)
        y_predicted = numpy.argmax(nn(X), axis=1)
        classification = [yi == yip for yi, yip in zip(y, y_predicted)]
        err = float(sum([not i for i in classification]))/len(classification)
        logging.info("Error: %0.2f (for %i training examples)", err, len(y))

    # Pre-segment to 8 strokes
    # TODO: Take first 4 strokes and add strokes within their bounding box
    # TODO: What if that is more then 8 strokes?

    # Segment after pre-segmentation
    prob = [[1.0 for _ in recording] for _ in recording]
    for strokeid1, stroke1 in enumerate(recording):
        for strokeid2, stroke2 in enumerate(recording):
            if strokeid1 == strokeid2:
                continue
            X = get_stroke_features(recording, strokeid1, strokeid2)
            X += X_symbol
            X = numpy.array([X], dtype=numpy.float32)
            prob[strokeid1][strokeid2] = stroke_segmented_classifier(X)
    logging.debug("len(recording)=%i", len(recording))
    logging.debug("len(prob)=%i", len(prob))

    import partitions
    return partitions.get_top_segmentations(prob, 500)


if __name__ == '__main__':
    import sys
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.DEBUG,
                        stream=sys.stdout)

    logging.info("Start doctest")
    import doctest
    doctest.testmod()
    logging.info("Get segmented raw data")
    recordings = get_segmented_raw_data()
    logging.info("Start testing")
    score_place = []
    for recording in recordings:
        seg_predict = get_segmentation(json.loads(recording['data']))
        real_seg = json.loads(recording['segmentation'])
        print("## %i" % recording['id'])
        print("Real segmentation:\t\t%s" % real_seg)
        for i, pred in enumerate(seg_predict):
            seg, score = pred
            if i == 0:
                print("Predict segmentation:\t%s (%0.8f)" % (seg, score))
            #print("#{0:>3} {1:.8f}: {2}".format(i, score, seg))
            if seg == real_seg:
                score_place.append(i)
                break
