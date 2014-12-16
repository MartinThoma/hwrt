#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import nose
import tests.testhelper as th

# hwrt modules
from hwrt.HandwrittenData import HandwrittenData
import hwrt.preprocessing as preprocessing
import hwrt.features as features
import hwrt.create_pfiles as create_pfiles
import hwrt.data_multiplication as data_multiplication
import hwrt.utils as utils


# Tests
def training_set_multiplication_test():
    sample = th.get_symbol_as_handwriting(292934)
    training_set = [{'id': 1337,
                     'is_in_testset': 0,
                     'formula_id': 42,
                     'handwriting': sample,
                     'formula_in_latex': 'B'}]
    mult_queue = [data_multiplication.Multiply()]
    create_pfiles.training_set_multiplication(training_set, mult_queue)
    # nose.tools.assert_equal(len(feature_list), len(correct))


def execution_test():
    formula_id2index = {1337: 1, 12: 2}
    feature_folder = '.'
    index2latex = {1: '\\alpha', 2: '\\beta'}
    create_pfiles._create_index_formula_lookup(formula_id2index,
                                               feature_folder,
                                               index2latex)


def parser_test():
    create_pfiles.get_parser()


def prepare_dataset_test():
    dataset = []
    for i in range(200):
        dataset.append({'handwriting': th.get_symbol_as_handwriting(97705),
                        'formula_id': 42})
    # dataset[-1]['handwriting'].formula_id = 42
    formula_id2index = {}
    formula_id2index[42] = 1
    feature_list = [features.StrokeCount()]
    is_traindata = False
    create_pfiles.prepare_dataset(dataset,
                                  formula_id2index,
                                  feature_list,
                                  is_traindata)


def normalize_features_one_test():
    feature_list = [features.Width(), features.Height()]
    prepared = [([123], 1)]
    is_traindata = True
    out = create_pfiles._normalize_features(feature_list,
                                            prepared,
                                            is_traindata)
    nose.tools.assert_equal(out, [([0.0], 1)])


def normalize_features_two_test():
    feature_list = [features.Width(), features.Height()]
    prepared = [([123], 1), ([100], 1)]
    is_traindata = True
    out = create_pfiles._normalize_features(feature_list,
                                            prepared,
                                            is_traindata)
    # Mean: 111.5; Range: 23
    nose.tools.assert_equal(out, [([0.5], 1), ([-0.5], 1)])

    # Now the other set
    prepared = [([111.5], 1), ([90], 1), ([180], 1)]
    is_traindata = False
    out = create_pfiles._normalize_features(feature_list,
                                            prepared,
                                            is_traindata)
    nose.tools.assert_equal(out, [([0.0], 1),
                                  ([-0.93478260869565222], 1),
                                  ([2.9782608695652173], 1)])


def normalize_features_two_feats_test():
    feature_list = [features.Width(), features.Height()]
    prepared = [([123, 123], 1), ([100, 100], 1)]
    is_traindata = True
    out = create_pfiles._normalize_features(feature_list,
                                            prepared,
                                            is_traindata)
    # Mean: 111.5; Range: 23
    nose.tools.assert_equal(out, [([0.5, 0.5], 1), ([-0.5, -0.5], 1)])

    # Now the other set
    prepared = [([111.5, 111.5], 1), ([146, 146], 1), ([54, 54], 1)]
    is_traindata = False
    out = create_pfiles._normalize_features(feature_list,
                                            prepared,
                                            is_traindata)
    nose.tools.assert_equal(out, [([0.0, 0.0], 1),
                                  ([1.5, 1.5], 1),
                                  ([-2.5, -2.5], 1)])


def normalize_features_two_feats2_test():
    feature_list = [features.Width(), features.Height()]
    prepared = [([123, 123], 1), ([100, 100], 1)]
    is_traindata = True
    out = create_pfiles._normalize_features(feature_list,
                                            prepared,
                                            is_traindata)
    # Mean: 111.5; Range: 23
    nose.tools.assert_equal(out, [([0.5, 0.5], 1), ([-0.5, -0.5], 1)])

    # Now the other set
    prepared = [([111.5, 146], 1), ([146, 111.5], 1), ([54, 54], 1)]
    is_traindata = False
    out = create_pfiles._normalize_features(feature_list,
                                            prepared,
                                            is_traindata)
    nose.tools.assert_equal(out, [([0.0, 1.5], 1),
                                  ([1.5, 0.0], 1),
                                  ([-2.5, -2.5], 1)])


def normalize_features_two_classes_test():
    feature_list = [features.Width(), features.Height()]
    prepared = [([123], 1), ([100], 1), ([500], 2)]
    is_traindata = True
    out = create_pfiles._normalize_features(feature_list,
                                            prepared,
                                            is_traindata)
    # Mean: 241; Range: 400
    nose.tools.assert_equal(out, [([-0.295], 1),
                                  ([-0.3525], 1),
                                  ([0.6475], 2)])


def create_translation_file_test():
    feature_folder = os.path.join(utils.get_project_root(),
                                  "feature-files",
                                  "small-baseline")
    dataset_name = "testtestdata"
    translation = [(133700, '\\alpha', 42)]
    formula_id2index = {42: 1}
    create_pfiles._create_translation_file(feature_folder,
                                           dataset_name,
                                           translation,
                                           formula_id2index)
