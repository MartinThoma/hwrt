#!/usr/bin/env python

"""
Create feature files.

Before this script is run, the `download.py` should get executed to generate
a handwriting_datasets.pickle with exactly those symbols that should also
be present in the feature files and only raw_data that might get used for the
test-, validation- and training set.
"""


# Core Library modules
import csv
import gc
import logging
import os
import pickle
import sys
import time
from collections import defaultdict

# Third party modules
import numpy
import yaml

# Local modules
# HandwrittenData and preprocessing are needed because of pickle
from . import handwritten_data  # noqa
from . import data_multiplication, features, preprocessing, utils

logger = logging.getLogger(__name__)


def _create_index_formula_lookup(formula_id2index, feature_folder, index2latex):
    """
    Create a lookup file where the index is mapped to the formula id and the
    LaTeX command.

    Parameters
    ----------
    formula_id2index : Dict
    feature_folder : str
        Path to a folder in which a feature file as well as an
        index2formula_id.csv is.
    index2latex : dict
        Maps an integer index to a LaTeX command
    """
    index2formula_id = sorted(list(formula_id2index.items()), key=lambda n: n[1])
    index2formula_file = os.path.join(feature_folder, "index2formula_id.csv")
    with open(index2formula_file, "w") as f:
        f.write("index,formula_id,latex\n")
        for formula_id, index in index2formula_id:
            f.write("%i,%i,%s\n" % (index, formula_id, index2latex[index]))


def _create_translation_file(
    feature_folder, dataset_name, translation, formula_id2index
):
    """
    Write a loop-up file that contains the direct (record-wise) lookup
    information.

    Parameters
    ----------
    feature_folder :
        Path to the feature files.
    dataset_name :
        'traindata', 'validdata' or 'testdata'.
    translation : list of triples
        (raw data id, formula in latex, formula id)
    """
    translationfilename = f"{feature_folder}/translation-{dataset_name}.csv"
    with open(translationfilename, "w") as f:
        f.write("index,raw_data_id,latex,formula_id\n")
        for el in translation:
            f.write("%i,%i,%s,%i\n" % (formula_id2index[el[2]], el[0], el[1], el[2]))


def main(feature_folder, create_learning_curve=False):
    """main function of create_ffiles.py"""

    # Read the feature description file
    with open(os.path.join(feature_folder, "info.yml")) as ymlfile:
        feature_description = yaml.safe_load(ymlfile)

    # Get preprocessed .pickle file from model description file
    path_to_data = os.path.join(
        utils.get_project_root(), feature_description["data-source"]
    )
    if os.path.isdir(path_to_data):
        path_to_data = os.path.join(path_to_data, "data.pickle")
    target_paths = {
        "traindata": os.path.join(feature_folder, "traindata.hdf5"),
        "validdata": os.path.join(feature_folder, "validdata.hdf5"),
        "testdata": os.path.join(feature_folder, "testdata.hdf5"),
    }

    feature_list = features.get_features(feature_description["features"])
    mult_queue = data_multiplication.get_data_multiplication_queue(
        feature_description["data-multiplication"]
    )

    # Set everything up for the creation of the 3 hdf5 (test, validation,
    # training).

    os.chdir(feature_folder)
    logger.info("Start creation of hdf5-files...")
    logger.info("Get sets from '%s' ...", path_to_data)
    (
        training_set,
        validation_set,
        test_set,
        formula_id2index,
        preprocessing_queue,
        index2latex,
    ) = get_sets(path_to_data)

    training_set = training_set_multiplication(training_set, mult_queue)
    _create_index_formula_lookup(formula_id2index, feature_folder, index2latex)

    # Output data for documentation
    print("Classes (nr of symbols): %i" % len(formula_id2index))
    preprocessing.print_preprocessing_list(preprocessing_queue)
    features.print_featurelist(feature_list)

    logger.info("Start creating hdf5 files")

    # Get the dimension of the feature vector
    input_features = sum([n.get_dimension() for n in feature_list])

    # Traindata has to come first because of feature normalization
    for dataset_name, dataset, is_traindata in [
        ("traindata", training_set, True),
        ("testdata", test_set, False),
        ("validdata", validation_set, False),
    ]:
        t0 = time.time()
        logger.info("Start preparing '%s' ...", dataset_name)
        prepared, translation = prepare_dataset(
            dataset, formula_id2index, feature_list, is_traindata
        )
        logger.info("%s length: %i", dataset_name, len(prepared))
        logger.info("start 'make_hdf5'x ...")
        make_hdf5(
            dataset_name,
            input_features,
            prepared,
            os.path.join(feature_folder, target_paths[dataset_name]),
            create_learning_curve,
        )

        _create_translation_file(
            feature_folder, dataset_name, translation, formula_id2index
        )

        t1 = time.time() - t0
        logger.info("%s was written. Needed %0.2f seconds", dataset_name, t1)
        gc.collect()
    utils.create_run_logfile(feature_folder)


def training_set_multiplication(training_set, mult_queue):
    """
    Multiply the training set by all methods listed in mult_queue.

    Parameters
    ----------
    training_set :
        set of all recordings that will be used for training
    mult_queue :
        list of all algorithms that will take one recording and generate more
        than one.

    Returns
    -------
    mutliple recordings
    """
    logger.info("Multiply data...")
    for algorithm in mult_queue:
        new_trning_set = []
        for recording in training_set:
            samples = algorithm(recording["handwriting"])
            for sample in samples:
                new_trning_set.append(
                    {
                        "id": recording["id"],
                        "is_in_testset": 0,
                        "formula_id": recording["formula_id"],
                        "handwriting": sample,
                        "formula_in_latex": recording["formula_in_latex"],
                    }
                )
        training_set = new_trning_set
    return new_trning_set


def get_sets(path_to_data):
    """
    Get a training, validation and a testset as well as a dictionary that maps
    each formula_id to an index (0...nr_of_formulas - 1).

    Parameters
    ----------
    path_to_data :
        A pickle file that contains a list of datasets.

    Returns
    -------
    tuple
        0: list
            The training_set contains recordings.
        1: list
            The validation_set contains recordings.
        2: list
            The test_set contains recordings.
        3: dict
            The formula_id2index maps write-math.com formula ids to
            an index which begins at 0.
        4: list
            The preprocessing_queue contains objects which encapsulate
            algorithms for preprocessing.
        5: dict
            The index2latex maps the index of the neural network to the latex
            command.
    """
    loaded = pickle.load(open(path_to_data, "rb"))
    datasets = loaded["handwriting_datasets"]

    training_set, validation_set, test_set = [], [], []

    dataset_by_formula_id = {}
    formula_id2index = {}
    index2latex = {}

    # Group data in dataset_by_formula_id so that 10% can be used for the
    # validation set
    for i, dataset in enumerate(datasets):
        if dataset["formula_id"] in dataset_by_formula_id:
            dataset_by_formula_id[dataset["formula_id"]].append(dataset)
        else:
            dataset_by_formula_id[dataset["formula_id"]] = [dataset]
        utils.print_status(len(datasets), i)
    print("")

    # Create the test-, validation- and training set
    print("Create the test-, validation- and training set")
    for formula_id, dataset in dataset_by_formula_id.items():
        tmp = dataset[0]["handwriting"].formula_in_latex
        index2latex[len(formula_id2index)] = tmp
        formula_id2index[formula_id] = len(formula_id2index)
        i = 0
        for raw_data in dataset:
            if raw_data["is_in_testset"]:
                test_set.append(raw_data)
            else:
                if i % 10 == 0:
                    validation_set.append(raw_data)
                else:
                    training_set.append(raw_data)
                i = (i + 1) % 10
    if "preprocessing_queue" in loaded:
        preprocessing_queue = loaded["preprocessing_queue"]
    else:
        preprocessing_queue = []
    return (
        training_set,
        validation_set,
        test_set,
        formula_id2index,
        preprocessing_queue,
        index2latex,
    )


def _calculate_feature_stats(
    feature_list, prepared, serialization_file
):  # pylint: disable=R0914
    """Calculate min, max and mean for each feature. Store it in object."""
    # Create feature only list
    feats = [x for x, _ in prepared]  # Label is not necessary

    # Calculate all means / mins / maxs
    means = numpy.mean(feats, 0)
    mins = numpy.min(feats, 0)
    maxs = numpy.max(feats, 0)

    # Calculate, min, max and mean vector for each feature with
    # normalization
    start = 0
    mode = "w"
    arguments = {"newline": ""}
    if sys.version_info.major < 3:
        mode += "b"
        arguments = {}
    with open(serialization_file, mode, **arguments) as csvfile:
        spamwriter = csv.writer(
            csvfile, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        for feature in feature_list:
            end = start + feature.get_dimension()
            # append the data to the feature class
            feature.mean = numpy.array(means[start:end])
            feature.min = numpy.array(mins[start:end])
            feature.max = numpy.array(maxs[start:end])
            start = end
            for mean, fmax, fmin in zip(feature.mean, feature.max, feature.min):
                spamwriter.writerow([mean, fmax - fmin])


def _normalize_features(feature_list, prepared, is_traindata):
    """Normalize features (subtract mean, division by variance or range)."""
    if is_traindata:
        _calculate_feature_stats(feature_list, prepared, "featurenormalization.csv")

    start = 0
    for feature in feature_list:
        end = start + feature.get_dimension()
        # For every instance in the dataset: Normalize!
        for i in range(len(prepared)):
            # The 0 is necessary as every element is (x, y)
            feature_range = feature.max - feature.min
            if feature_range == 0:
                feature_range = 1
            prepared[i][0][start:end] = (
                prepared[i][0][start:end] - feature.mean
            ) / feature_range
        start = end
    return prepared


def prepare_dataset(
    dataset, formula_id2index, feature_list, is_traindata, do_normalization=False
):
    """Transform each instance of dataset to a (Features, Label) tuple."""
    prepared = []
    start_time = time.time()
    translation = []
    for i, data in enumerate(dataset):
        x = []
        handwriting = data["handwriting"]
        x = handwriting.feature_extraction(feature_list)  # Feature selection
        y = formula_id2index[data["formula_id"]]  # Get label
        translation.append(
            (
                handwriting.raw_data_id,
                handwriting.formula_in_latex,
                handwriting.formula_id,
            )
        )
        prepared.append((numpy.array(x), y))
        if i % 100 == 0 and i > 0:
            utils.print_status(len(dataset), i, start_time)
    sys.stdout.write("\r100%" + " " * 80 + "\n")
    sys.stdout.flush()

    # Feature normalization
    if do_normalization:
        _normalize_features(feature_list, prepared, is_traindata)
    return (prepared, translation)


def make_hdf5(
    dataset_name, feature_count, data, output_filename, create_learning_curve
):
    """
    Create the hdf5 file.

    Parameters
    ----------
    filename :
        name of the file that hdf5_create will use to create the hdf5 file.
    feature_count : integer
        number of features
    data : list of tuples
         data format ('feature_string', 'label')
    """
    # create raw data file for hdf5_create
    if dataset_name == "traindata" and create_learning_curve:
        max_trainingexamples = 501
        output_filename_save = output_filename
        steps = 10
        for trainingexamples in range(100, max_trainingexamples, steps):
            # adjust output_filename
            tmp = output_filename_save.split(".")
            tmp[-2] += "-%i-examples" % trainingexamples
            output_filename = ".".join(map(str, tmp))

            # Make sure the data has not more than ``trainingexamples``
            seen_symbols = defaultdict(int)
            new_data = {}
            for feature_string, label in data:
                if seen_symbols[label] < trainingexamples:
                    seen_symbols[label] += 1
                    new_data = (feature_string, label)

            # Create the hdf5 file
            utils.create_hdf5(output_filename, feature_count, new_data)
    else:
        utils.create_hdf5(output_filename, feature_count, data)
