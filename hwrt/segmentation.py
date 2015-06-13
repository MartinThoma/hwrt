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
import pkg_resources

import time

import scipy.sparse.csgraph

# hwrt modules
# from . import HandwrittenData
from hwrt import utils
from hwrt.HandwrittenData import HandwrittenData
from hwrt import features
from hwrt import geometry
from hwrt import partitions


def main():
    logging.info("Get single classifier")
    single_clf = single_classifier()

    logging.info("Get stroke_segmented_classifier "
                 "(decided if two strokes are in one symbol)")
    logging.info("Start creation of training set")
    X, y, recordings = get_dataset()
    logging.info("Start training")
    nn = get_nn_classifier(X, y)
    stroke_segmented_classifier = lambda X: nn(X)[0][1]
    y_predicted = numpy.argmax(nn(X), axis=1)
    classification = [yi == yip for yi, yip in zip(y, y_predicted)]
    err = float(sum([not i for i in classification]))/len(classification)
    logging.info("Error: %0.2f (for %i training examples)", err, len(y))

    logging.info("Get single stroke classifier")
    single_stroke_clf = None  # single_symbol_stroke_classifier()

    logging.info("Start testing")
    score_place = []
    out_of_order_count = 0
    ## Filter recordings
    #recordings = filter_recordings(recordings)
    over_segmented_symbols = 0
    under_segmented_symbols = 0
    overunder_segmented_symbols = 0

    for nr, recording in enumerate(recordings):
        if nr % 100 == 0:
            print(("## %i " % nr) + "#"*80)

        t0 = time.time()
        seg_predict = get_segmentation(recording['data'],
                                       single_clf,
                                       single_stroke_clf,
                                       stroke_segmented_classifier)
        t1 = time.time()
        real_seg = recording['segmentation']
        if all([has_wrong_break(real_seg, seg) for seg, score in seg_predict]):
            over_segmented_symbols += 1
        if all([has_missing_break(real_seg, seg) for seg, score in seg_predict]):
            under_segmented_symbols += 1
        if all([has_wrong_break(real_seg, seg) for seg, score in seg_predict]) \
           and all([has_missing_break(real_seg, seg) for seg, score in seg_predict]):
           overunder_segmented_symbols += 1
        pred_str = ""
        for i, pred in enumerate(seg_predict):
            seg, score = pred
            if i == 0:
                pred_str = "  Predict segmentation:\t%s (%0.8f)" % (seg, score)
            #print("#{0:>3} {1:.8f}: {2}".format(i, score, seg))
            if seg == real_seg:
                score_place.append(i)
                break
        else:
            i = -1
            score_place.append(10**6)
        if all([has_wrong_break(real_seg, seg) for seg, score in seg_predict]):
            print("## %i" % recording['id'])
            print("  Real segmentation:\t%s (got at place %i)" % (real_seg, i))
            print(pred_str)
            print("  Segmentation took %0.4f seconds." % (t1-t0))
            if has_wrong_break(real_seg, seg_predict[0][0]):
                print("  over-segmented")
            if has_missing_break(real_seg, seg_predict[0][0]):
                print("  under-segmented")
        out_of_order_count += _is_out_of_order(real_seg)
    logging.info("mean: %0.2f", numpy.mean(score_place))
    logging.info("median: %0.2f", numpy.median(score_place))
    logging.info("TOP-1: %0.2f", _less_than(score_place, 1)/len(recordings))
    logging.info("TOP-3: %0.2f", _less_than(score_place, 3)/len(recordings))
    logging.info("TOP-10: %0.2f", _less_than(score_place, 10)/len(recordings))
    logging.info("TOP-20: %0.2f", _less_than(score_place, 20)/len(recordings))
    logging.info("TOP-50: %0.2f", _less_than(score_place, 50)/len(recordings))
    logging.info("Over-segmented: %0.2f", float(over_segmented_symbols)/len(recordings))
    logging.info("Under-segmented: %0.2f", float(under_segmented_symbols)/len(recordings))
    logging.info("overUnder-segmented: %0.2f", float(overunder_segmented_symbols)/len(recordings))
    logging.info("Out of order: %i", out_of_order_count)
    logging.info("Total: %i", len(recordings))


class single_classifier(object):
    """Classifier for single symbols."""
    def __init__(self):
        logging.info("Start reading model...")
        model_path = pkg_resources.resource_filename('hwrt', 'misc/')
        model_file = os.path.join(model_path, "model.tar")
        logging.info("Model: %s", model_file)
        (preprocessing_queue, feature_list, model,
         output_semantics) = utils.load_model(model_file)
        self.preprocessing_queue = preprocessing_queue
        self.feature_list = feature_list
        self.model = model
        self.output_semantics = output_semantics

    def predict(self, parsed_json):
        evaluate = utils.evaluate_model_single_recording_preloaded
        results = evaluate(self.preprocessing_queue,
                           self.feature_list,
                           self.model,
                           self.output_semantics,
                           json.dumps(parsed_json['data']),
                           parsed_json['id'])
        return results


def get_dataset():
    """Create a dataset for machine learning.

    Returns
    -------
    tuple :
        (X, y) where X is a list of tuples. Each tuple is a feature. y
        is a list of labels (0 for 'not in one symbol' and 1 for 'in symbol')
    """
    seg_data = "segmentation-X.npy"
    seg_labels = "segmentation-y.npy"
    #seg_ids = "segmentation-ids.npy"
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
    datasets = filter_recordings(datasets)
    with open('datasets.pickle', 'wb') as f:
        pickle.dump(datasets, f, protocol=pickle.HIGHEST_PROTOCOL)
    return (X, y, datasets)


def _get_symbol_index(stroke_id_needle, segmentation):
    """
    Parameters
    ----------
    stroke_id_needle : int
        Identifier for the stroke of which the symbol should get found.
    segmentation : list of lists of integers
        An ordered segmentation of strokes to symbols.

    Returns
    -------
    The symbol index in which stroke_id_needle occurs

    Examples
    --------
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
    """Fetch data from the server."""
    import pymysql.cursors
    cfg = utils.get_database_configuration()
    mysql = cfg['mysql_online']
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


def filter_recordings(recordings):
    """Remove all recordings which have points without time.
    Parameters
    ----------
    recordings : list of dicts
        Each dictionary has the keys 'data' and 'segmentation'

    Returns
    -------
    list of dicts :
        Only recordings where all points have time values.
    """
    new_recordings = []
    for recording in recordings:
        recording['data'] = json.loads(recording['data'])
        tmp = json.loads(recording['segmentation'])
        recording['segmentation'] = normalize_segmentation(tmp)
        had_none = False
        for stroke in recording['data']:
            for point in stroke:
                if point['time'] is None:
                    logging.debug("Had None-time: %i", recording['id'])
                    had_none = True
                    break
            if had_none:
                break
        if not had_none:
            new_recordings.append(recording)

    recordings = new_recordings
    logging.info("Done filtering")
    return recordings


def get_nn_classifier(X, y):
    """Train a neural network classifier.

    Parameters
    ----------
    X : numpy array
        A list of feature vectors
    y : numpy array
        A list of labels

    Returns
    -------
    Theano expression :
        The trained neural network
    """
    import lasagne
    import theano
    import theano.tensor as T
    N_CLASSES = 2

    nn_pickled_filename = 'is_one_symbol_classifier.pickle'
    if os.path.isfile(nn_pickled_filename):
        with open(nn_pickled_filename, 'rb') as handle:
            get_output = pickle.load(handle)
    else:
        # First, construct an input layer. The shape parameter defines the
        # expected input shape, which is just the shape of our data matrix X.
        l_in = lasagne.layers.InputLayer(shape=X.shape)
        # A dense layer implements a linear mix (xW + b) followed by a
        # nonlinear function.
        hiddens = [64, 64, 64]  # sollte besser als 0.12 sein (mit [32])
        layers = [l_in]

        for n_units in hiddens:
            l_hidden_1 = lasagne.layers.DenseLayer(
                layers[-1],  # The first argument is the input to this layer
                num_units=n_units,  # the layer's output dimensionality
                nonlinearity=lasagne.nonlinearities.tanh)
            layers.append(l_hidden_1)
        # For our output layer, we'll use a dense layer with a softmax
        # nonlinearity.
        l_output = lasagne.layers.DenseLayer(layers[-1], num_units=N_CLASSES,
                                             nonlinearity=lasagne.nonlinearities.softmax)
        # Now, we can generate the symbolic expression of the network's output
        # given an input variable.
        net_input = T.matrix('net_input')
        net_output = l_output.get_output(net_input)
        # As a loss function, we'll use Theano's categorical_crossentropy
        # function. This allows for the network output to be class
        # probabilities, but the target output to be class labels.
        true_output = T.ivector('true_output')
        loss = T.mean(T.nnet.categorical_crossentropy(net_output, true_output))

        reg = lasagne.regularization.l2(l_output)
        loss = loss + 0.001*reg
        #NLL_LOSS = -T.sum(T.log(p_y_given_x)[T.arange(y.shape[0]), y])
        # Retrieving all parameters of the network is done using
        # get_all_params, which recursively collects the parameters of all
        # layers connected to the provided layer.
        all_params = lasagne.layers.get_all_params(l_output)

        # Now, we'll generate updates using Lasagne's SGD function
        updates = lasagne.updates.momentum(loss, all_params, learning_rate=0.1)

        # Finally, we can compile Theano functions for training and computing
        # the output.
        train = theano.function([net_input, true_output], loss, updates=updates)
        get_output = theano.function([net_input], net_output)

        logging.debug("|X|=%i", len(X))
        logging.debug("|y|=%i", len(y))
        logging.debug("|X[0]|=%i", len(X[0]))

        # Train
        epochs = 20
        for n in range(epochs):
            train(X, y)
        with open(nn_pickled_filename, 'wb') as handle:
            pickle.dump(get_output, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return get_output


def get_stroke_features(recording, strokeid1, strokeid2):
    """Get the features used to decide if two strokes belong to the same symbol
    or not.

    Parameters
    ----------
    recording : list
        A list of strokes
    strokeid1 : int
    strokeid2 : int

    Returns
    -------
    list :
        A list of features which could be useful to decide if stroke1 and
        stroke2 belong to the same symbol.
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
    # X_i += [get_black_percentage()]
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

    min_dist = geometry.segments_distance(stroke1[0], stroke2[0])
    for seg1, seg2 in itertools.product(stroke1, stroke2):
        min_dist = min(min_dist, geometry.segments_distance(seg1, seg2))
    return min_dist


def merge_segmentations(segs1, segs2, strokes=None):
    """
    Parameters
    ----------
    segs1 : a list of tuples
        Each tuple is a segmentation with its score
    segs2 : a list of tuples
        Each tuple is a segmentation with its score
    strokes : list of stroke names for segs2

    Returns
    -------
    list of tuples :
        Segmentations with their score, combined from segs1 and segs2
    """
    def translate(segmentation, strokes):
        t = []
        for symbol in segmentation:
            symbol_new = []
            for stroke in symbol:
                symbol_new.append(strokes[stroke])
            t.append(symbol_new)
        return t
    if strokes is None:
        strokes = [i for i in range(len(segs2[0][0]))]
    topf = partitions.TopFinder(500)
    for s1, s2 in itertools.product(segs1, segs2):
        topf.push(s1[0]+translate(s2[0], strokes), s1[1]*s2[1])
    return list(topf)


def update_segmentation_data(segmentation, add):
    return [[el + add for el in symbol] for symbol in segmentation]


def get_segmentation(recording,
                     single_clf,
                     single_stroke_clf,
                     stroke_segmented_classifier):
    """Get a list of segmentations of recording with the probability of the
    segmentation being correct.

    Parameters
    ----------
    recording : A list of lists
        Each sublist represents a stroke
    single_clf : object
        A classifier for single symbols
    single_stroke_clf : object
        A classifier which decides if a single stroke is a complete symbol
    stroke_segmented_classifier : object
        Classifier which decides if two strokes belong to one symbol or not

    Returns
    -------
    list of tuples :
        Segmentations together with their probabilities. Each probability
        has to be positive and the sum may not be bigger than 1.0.

    Examples
    --------
    >>> stroke1 = [{'x': 0, 'y': 0, 'time': 0}, {'x': 12, 'y': 12, 'time': 1}]
    >>> stroke2 = [{'x': 0, 'y': 10, 'time': 2}, {'x': 12, 'y': 0, 'time': 3}]
    >>> stroke3 = [{'x': 14, 'y': 0, 'time': 5}, {'x': 14, 'y': 12, 'time': 6}]
    >>> #get_segmentation([stroke1, stroke2, stroke3], single_clf)
    [
      ([[0, 1], [2]], 0.8),
      ([[0], [1,2]], 0.1),
      ([[0,2], [1]], 0.05)
    ]
    """

    # TODO: Use the mst
    points = get_points(recording)
    mst = get_mst(points)
    mst_wood = [{'mst': mst, 'strokes': list(range(len(mst)))}]
    # TODO: break mst into wood of msts wherever possible by recognizing single
    # symbols by stroke

    bbintersections = get_bb_intersections(recording)
    for i, stroke in enumerate(recording):  # TODO
        predictions = single_clf.predict({'id': 0, 'data': [stroke]})
        prob_sum = sum([p['probability'] for p in predictions])  # TODO predictions[:20]
        # dots cannot be segmented into single symbols at this point
        if prob_sum > 0.95 and not any([el for el in bbintersections[i]]) and len(stroke) > 2 and predictions[0]['semantics'].split(';')[1] != '-':
            # Split mst here
            split_mst_index, split_node_i = find_split_node(mst_wood, i)
            mst_wood_tmp = break_mst(mst_wood[split_mst_index],
                                     split_node_i)
            del mst_wood[split_mst_index]
            for mst in mst_wood_tmp:
                mst_wood.append(mst)
            for mst in mst_wood:
                if i in mst['strokes']:
                    mst['pred'] = predictions[0]['semantics'].split(';')[1]

    # if any([True for mst in mst_wood if len(mst['strokes']) >= 8]):
    #     logging.debug([mst['pred'] for mst in mst_wood if 'pred' in mst])
    #     HandwrittenData(json.dumps(recording)).show()
    return [(normalize_segmentation([mst['strokes'] for mst in mst_wood]), 1.0)]

    # HandwrittenData(json.dumps(recording)).show()
    # return [([[i for i in range(len(recording))]], 1.0)]
    ##mst_wood = break_mst(mst, recording)  # TODO

    # for i in range(0, 2**len(points)):
    #     segmentation = get_segmentation_from_mst(mst, i)
    # TODO

    X_symbol = [get_median_stroke_distance(recording)]

    # Pre-segment to 8 strokes
    # TODO: Take first 4 strokes and add strokes within their bounding box
    # TODO: What if that is more then 8 strokes?
    # -> Geometry
    #    Build tree structure. A stroke `c` is the child of another stroke `p`,
    #    if the bounding box of `c` is within the bounding box of `p`.
    #       Problem: B <-> 13
    top_segmentations_global = [([], 1.0)]
    for chunk_part in mst_wood:  # range(int(math.ceil(float(len(recording))/8))):
        #chunk = recording[8*chunk_part:8*(chunk_part+1)]
        chunk = [recording[stroke] for stroke in chunk_part['strokes']]

        # Segment after pre-segmentation
        prob = [[1.0 for _ in chunk] for _ in chunk]
        for strokeid1 in range(len(chunk)):
            for strokeid2 in range(len(chunk)):
                if strokeid1 == strokeid2:
                    continue
                X = get_stroke_features(chunk, strokeid1, strokeid2)
                X += X_symbol
                X = numpy.array([X], dtype=numpy.float32)
                prob[strokeid1][strokeid2] = stroke_segmented_classifier(X)

        top_segmentations = list(partitions.get_top_segmentations(prob, 500))
        for i, segmentation in enumerate(top_segmentations):
            symbols = apply_segmentation(chunk, segmentation)
            min_top2 = partitions.TopFinder(1, find_min=True)
            for i, symbol in enumerate(symbols):
                predictions = single_clf.predict(symbol)
                min_top2.push("value-%i" % i,
                              predictions[0]['probability'] +
                              predictions[1]['probability'])
            top_segmentations[i][1] *= list(min_top2)[0][1]
        # for i, segmentation in enumerate(top_segmentations):
        #     top_segmentations[i][0] = update_segmentation_data(top_segmentations[i][0], 8*chunk_part)
        top_segmentations_global = merge_segmentations(top_segmentations_global, top_segmentations, chunk_part['strokes'])
    return [(normalize_segmentation(seg), prob) for seg, prob in top_segmentations_global]


def has_missing_break(real_seg, pred_seg):
    """
    Parameters
    ----------
    real_seg : list of integers
        The segmentation as it should be.
    pred_seg : list of integers
        The predicted segmentation.

    Returns
    -------
    bool :
        True, if strokes of two different symbols are put in the same symbol.
    """
    for symbol_pred in pred_seg:
        for symbol_real in real_seg:
            if symbol_pred[0] in symbol_real:
                for stroke in symbol_pred:
                    if stroke not in symbol_real:
                        return True
    return False


def has_wrong_break(real_seg, pred_seg):
    """
    Parameters
    ----------
    real_seg : list of integers
        The segmentation as it should be.
    pred_seg : list of integers
        The predicted segmentation.

    Returns
    -------
    bool :
        True, if strokes of one symbol were segmented to be in different
        symbols.
    """
    for symbol_real in real_seg:
        for symbol_pred in pred_seg:
            if symbol_real[0] in symbol_pred:
                for stroke in symbol_real:
                    if stroke not in symbol_pred:
                        return True
    return False


def find_split_node(mst_wood, i):
    """
    Parameters
    ----------
    mst_wood : list of dictionarys
    i : int
        Number of the stroke where one mst gets split

    Returns
    -------
    tuple :
        (mst index, node index)
    """
    for mst_index, mst in enumerate(mst_wood):
        if i in mst['strokes']:
            return (mst_index, mst['strokes'].index(i))
    raise ValueError('%i was not found as stroke index.' % i)


def break_mst(mst, i):
    """Break mst into multiple MSTs by removing one node i.

    Parameters
    ----------
    mst : symmetrical square matrix
    i : index of the mst where to break

    Returns
    -------
    list of dictionarys ('mst' and 'strokes' are the keys)
    """
    for j in range(len(mst['mst'])):
        mst['mst'][i][j] = 0
        mst['mst'][j][i] = 0
    _, components = scipy.sparse.csgraph.connected_components(mst['mst'])
    comp_indices = {}
    for el in set(components):
        comp_indices[el] = {'strokes': [], 'strokes_i': []}
    for i, comp_nr in enumerate(components):
        comp_indices[comp_nr]['strokes'].append(mst['strokes'][i])
        comp_indices[comp_nr]['strokes_i'].append(i)

    mst_wood = []

    for key in comp_indices:
        matrix = []
        for i, line in enumerate(mst['mst']):
            line_add = []
            if i not in comp_indices[key]['strokes_i']:
                continue
            for j, el in enumerate(line):
                if j in comp_indices[key]['strokes_i']:
                    line_add.append(el)
            matrix.append(line_add)
        assert len(matrix) > 0, \
            ("len(matrix) == 0 (strokes: %s, mst=%s, i=%i)" %
             (comp_indices[key]['strokes'], mst, i))
        assert len(matrix) == len(matrix[0]), \
            ("matrix was %i x %i, but should be square" %
             (len(matrix), len(matrix[0])))
        assert len(matrix) == len(comp_indices[key]['strokes']), \
            (("stroke length was not equal to matrix length "
              "(strokes=%s, len(matrix)=%i)") %
             (comp_indices[key]['strokes'], len(matrix)))
        mst_wood.append({'mst': matrix,
                         'strokes': comp_indices[key]['strokes']})
    return mst_wood


def _is_out_of_order(segmentation):
    """
    Check if a given segmentation is out of order.

    Examples
    --------
    >>> _is_out_of_order([[0, 1, 2, 3]])
    False
    >>> _is_out_of_order([[0, 1], [2, 3]])
    False
    >>> _is_out_of_order([[0, 1, 3], [2]])
    True
    """
    last_stroke = -1
    for symbol in segmentation:
        for stroke in symbol:
            if last_stroke > stroke:
                return True
            last_stroke = stroke
    return False


def _less_than(l, n):
    return float(len([1 for el in l if el < n]))


class single_symbol_stroke_classifier(object):
    """Classifier which decides if a single stroke is a single symbol."""
    def __init__(self):
        logging.info("Start reading model...")
        model_path = pkg_resources.resource_filename('hwrt', 'misc/')
        model_file = os.path.join(model_path, "model-single-stroke.tar")  # TODO
        logging.info("Model: %s", model_file)
        (preprocessing_queue, feature_list, model,
         output_semantics) = utils.load_model(model_file)
        self.preprocessing_queue = preprocessing_queue
        self.feature_list = feature_list
        self.model = model
        self.output_semantics = output_semantics

    def predict(self, parsed_json):
        evaluate = utils.evaluate_model_single_recording_preloaded
        results = evaluate(self.preprocessing_queue,
                           self.feature_list,
                           self.model,
                           self.output_semantics,
                           json.dumps(parsed_json['data']),
                           parsed_json['id'])
        return results


def apply_segmentation(recording, segmentation):
    symbols = []
    seg, prob = segmentation
    for symbol_indices in seg:
        symbol = []
        for index in symbol_indices:
            symbol.append(recording[index])
        symbols.append({'data': symbol, 'id': 'symbol-%i' % index})
    return symbols


class Graph(object):
    def __init__(self):
        self.nodes = []

    def add_node(self, payload):
        """
        Returns
        -------
        int
            Identifier for the inserted node.
        """
        self.nodes.append(Node(len(self.nodes), payload))
        return len(self.nodes) - 1

    def add_edge(self, node_i, node_j):
        self.nodes[node_i].neighbors.append(self.nodes[node_j])
        self.nodes[node_j].neighbors.append(self.nodes[node_i])

    def get_connected_nodes(self):
        remaining_graph_nodes = list(range(len(self.nodes)))
        segments = []
        while len(remaining_graph_nodes) > 0:
            node_nr = remaining_graph_nodes.pop()
            segment = []
            queued = [node_nr]
            while len(queued) > 0:
                current = queued.pop()
                segment.append(current)
                remaining_graph_nodes.remove(current)
                queued = [n.identifier for n in self.nodes[current].neighbors
                          if n.identifier in remaining_graph_nodes]
            segments.append(segment)
        return segments

    def generate_euclidean_edges(self):
        n = len(self.nodes)
        self.w = numpy.zeros(shape=(n, n))
        for i in range(n):
            for j in range(n):
                self.w[i][j] = self.nodes[i].get().dist_to(self.nodes[j].get())


class Node(object):
    def __init__(self, identifier, payload):
        self.neighbors = []
        self.payload = payload
        self.identifier = identifier

    def add_neighbor(self, neighbor_node):
        self.neighbors.append(neighbor_node)

    def get(self):
        return self.payload


def get_segmentation_from_mst(mst, number):
    """Get a segmentation from a MST

    If the MST has 5 strokes and a spanning tree like
    1-\
       3-4-5
    2-/
    the number 3 (0011) would mean that the 0th edge
    and the 1st edge get cut. Lets say that the edge 0 is next to node 1 and
    edge 1 is next to node 2. Then the resulting segmentation would be
    [[1], [2], [3, 4, 5]]

    Parameters
    ----------
    mst :
        Minimum spanning tree
    number : int ({0, ..., 2^(edges in MST)-1})
        The number of the segmentation.
    """
    pass


def get_points(recording):
    """Get one point for each stroke in a recording. The point represents the
    strokes spacial position (e.g. the center of the bounding box).

    Parameters
    ----------
    recording : list of strokes

    Returns
    -------
    list :
        points
    """
    points = []
    for stroke in recording:
        point = geometry.get_bounding_box(stroke).get_center()
        points.append(point)
    return points


def get_bb_intersections(recording):
    """Get all intersections of the bounding boxes of strokes.

    Parameters
    ----------
    recording : list of lists of integers

    Returns
    -------
    A symmetrical matrix which indicates if two bounding boxes intersect.
    """
    intersections = numpy.zeros((len(recording), len(recording)),
                                dtype=bool)
    for i in range(len(recording)-1):
        a = geometry.get_bounding_box(recording[i]).grow(0.2)
        for j in range(i+1, len(recording)):
            b = geometry.get_bounding_box(recording[j]).grow(0.2)
            intersections[i][j] = geometry.do_bb_intersect(a, b)
            intersections[j][i] = intersections[i][j]
    return intersections


def get_mst(points):
    """
    Parameters
    ----------
    points : list of points (geometry.Point)
        The first element of the list is the center of the bounding box of the
        first stroke, the second one belongs to the seconds stroke, ...

    Returns
    -------
    mst : square matrix
        0 nodes the edges are not connected, > 0 means they are connected
    """
    graph = Graph()
    for point in points:
        graph.add_node(point)
    graph.generate_euclidean_edges()
    matrix = scipy.sparse.csgraph.minimum_spanning_tree(graph.w)
    mst = matrix.toarray().astype(int)
    # returned matrix is not symmetrical! make it symmetrical
    for i in range(len(mst)):
        for j in range(len(mst)):
            if mst[i][j] > 0:
                mst[j][i] = mst[i][j]
            if mst[j][i] > 0:
                mst[i][j] = mst[j][i]
    return mst


def normalize_segmentation(seg):
    """Bring the segmentation into order.

    Parameters
    ----------
    seg : list of lists of ints

    Returns
    -------
    seg : list of lists of ints

    Examples
    --------
    >>> normalize_segmentation([[5, 2], [1, 4, 3]])
    [[1, 3, 4], [2, 5]]
    """
    return sorted([sorted(el) for el in seg])


if __name__ == '__main__':
    import sys
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.DEBUG,
                        stream=sys.stdout)

    logging.info("Start doctest")
    import doctest
    doctest.testmod()

    main()
