#!/usr/bin/env python

# Core Library modules
import os

# First party modules
import hwrt.create_ffiles as create_ffiles
import hwrt.data_multiplication as data_multiplication
import hwrt.features as features
import hwrt.utils as utils
import tests.testhelper as th


def test_training_set_multiplication():
    """Test the create_ffiles.training_set_multiplication method."""
    sample = th.get_symbol_as_handwriting(292934)
    training_set = [
        {
            "id": 1337,
            "is_in_testset": 0,
            "formula_id": 42,
            "handwriting": sample,
            "formula_in_latex": "B",
        }
    ]
    mult_queue = [data_multiplication.Multiply()]
    create_ffiles.training_set_multiplication(training_set, mult_queue)


def test_execution():
    formula_id2index = {1337: 1, 12: 2}
    feature_folder = "."
    index2latex = {1: "\\alpha", 2: "\\beta"}
    create_ffiles._create_index_formula_lookup(
        formula_id2index, feature_folder, index2latex
    )


def test_prepare_dataset():
    """Test create_ffiles.prepare_dataset."""
    dataset = []
    for i in range(200):
        dataset.append(
            {"handwriting": th.get_symbol_as_handwriting(97705), "formula_id": 42}
        )
    # dataset[-1]['handwriting'].formula_id = 42
    formula_id2index = {}
    formula_id2index[42] = 1
    feature_list = [features.StrokeCount()]
    is_traindata = False
    create_ffiles.prepare_dataset(dataset, formula_id2index, feature_list, is_traindata)


def test_normalize_features_one():
    """Test create_ffiles._normalize_features with one point."""
    feature_list = [features.Width(), features.Height()]
    prepared = [([123], 1)]
    is_traindata = True
    out = create_ffiles._normalize_features(feature_list, prepared, is_traindata)
    assert out == [([0.0], 1)]


def test_normalize_features_two():
    """Test create_ffiles._normalize_features with two points."""
    feature_list = [features.Width(), features.Height()]
    prepared = [([123], 1), ([100], 1)]
    is_traindata = True
    out = create_ffiles._normalize_features(feature_list, prepared, is_traindata)
    # Mean: 111.5; Range: 23
    assert out == [([0.5], 1), ([-0.5], 1)]

    # Now the other set
    prepared = [([111.5], 1), ([90], 1), ([180], 1)]
    is_traindata = False
    out = create_ffiles._normalize_features(feature_list, prepared, is_traindata)
    assert out == [([0.0], 1), ([-0.93478260869565222], 1), ([2.9782608695652173], 1)]


def test_normalize_features_two_feats():
    """Test create_ffiles._normalize_features with two points."""
    feature_list = [features.Width(), features.Height()]
    prepared = [([123, 123], 1), ([100, 100], 1)]
    is_traindata = True
    out = create_ffiles._normalize_features(feature_list, prepared, is_traindata)
    # Mean: 111.5; Range: 23
    assert out == [([0.5, 0.5], 1), ([-0.5, -0.5], 1)]

    # Now the other set
    prepared = [([111.5, 111.5], 1), ([146, 146], 1), ([54, 54], 1)]
    is_traindata = False
    out = create_ffiles._normalize_features(feature_list, prepared, is_traindata)
    assert out == [([0.0, 0.0], 1), ([1.5, 1.5], 1), ([-2.5, -2.5], 1)]


def test_normalize_features_two_feats2():
    """Test create_ffiles._normalize_features with two points."""
    feature_list = [features.Width(), features.Height()]
    prepared = [([123, 123], 1), ([100, 100], 1)]
    is_traindata = True
    out = create_ffiles._normalize_features(feature_list, prepared, is_traindata)
    # Mean: 111.5; Range: 23
    assert out == [([0.5, 0.5], 1), ([-0.5, -0.5], 1)]

    # Now the other set
    prepared = [([111.5, 146], 1), ([146, 111.5], 1), ([54, 54], 1)]
    is_traindata = False
    out = create_ffiles._normalize_features(feature_list, prepared, is_traindata)
    assert out == [([0.0, 1.5], 1), ([1.5, 0.0], 1), ([-2.5, -2.5], 1)]


def test_normalize_features_two_classes():
    """Test create_ffiles._normalize_features with two classes."""
    feature_list = [features.Width(), features.Height()]
    prepared = [([123], 1), ([100], 1), ([500], 2)]
    is_traindata = True
    out = create_ffiles._normalize_features(feature_list, prepared, is_traindata)
    # Mean: 241; Range: 400
    assert out == [([-0.295], 1), ([-0.3525], 1), ([0.6475], 2)]


def test_create_translation_file():
    """Test create_ffiles._create_translation_file."""
    feature_folder = os.path.join(
        utils.get_project_root(), "feature-files", "small-baseline"
    )
    dataset_name = "testtestdata"
    translation = [(133700, "\\alpha", 42)]
    formula_id2index = {42: 1}
    create_ffiles._create_translation_file(
        feature_folder, dataset_name, translation, formula_id2index
    )
