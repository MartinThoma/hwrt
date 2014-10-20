#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Create pfiles.

Before this script is run, the `download.py` should get executed to generate
a handwriting_datasets.pickle with exactly those symbols that should also
be present in the pfiles and only raw_data that might get used for the
test-, validation- and training set.
"""

from __future__ import print_function
import logging
import sys
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)
import os
import csv
import cPickle as pickle
import time
import gc
import utils
import yaml
import numpy
from collections import defaultdict
# mine
from HandwrittenData import HandwrittenData  # Needed because of pickle
import preprocessing  # Needed because of pickle
import preprocess_dataset
import features
import data_multiplication


def main(feature_folder, create_learning_curve=False):
    PROJECT_ROOT = utils.get_project_root()

    # Read the feature description file
    with open(os.path.join(feature_folder, "info.yml"), 'r') as ymlfile:
        feature_description = yaml.load(ymlfile)

    # Get preprocessed .pickle file from model description file
    path_to_data = os.path.join(PROJECT_ROOT,
                                feature_description['data-source'])
    if os.path.isdir(path_to_data):
        path_to_data = os.path.join(path_to_data, "data.pickle")
    target_paths = {'traindata': os.path.join(feature_folder,
                                              "traindata.pfile"),
                    'validdata': os.path.join(feature_folder,
                                              "validdata.pfile"),
                    'testdata': os.path.join(feature_folder,
                                             "testdata.pfile")}

    # Get a list of all used features
    feature_list = features.get_features(feature_description['features'])

    # Get the list of data multiplication algorithms
    mult_queue = data_multiplication.get_data_multiplication_queue(
        feature_description['data-multiplication'])

    # Set everything up for the creation of the 3 pfiles (test, validation,
    # training).

    os.chdir(feature_folder)
    logging.info("Start creation of pfiles...")
    logging.info("Get sets from '%s' ..." % path_to_data)
    (training_set, validation_set, test_set, formula_id2index,
     preprocessing_queue, index2latex) = get_sets(path_to_data)

    # Multiply traing_set
    training_set = training_set_multiplication(training_set, mult_queue)

    # Write formula_id2index for later lookup
    index2formula_id = sorted(formula_id2index.items(), key=lambda n: n[1])
    index2formula_file = os.path.join(feature_folder, "index2formula_id.csv")
    with open(index2formula_file, "w") as f:
        f.write("index,formula_id,latex\n")
        for formula_id, index in index2formula_id:
            f.write("%i,%i,%s\n" % (index, formula_id, index2latex[index]))

    # Get the dimension of the feature vector
    INPUT_FEATURES = sum(map(lambda n: n.get_dimension(), feature_list))

    # Output data for documentation
    print("Classes (nr of symbols): %i" % len(formula_id2index))

    print("#### Preprocessing")
    print("```")
    for algorithm in preprocessing_queue:
        print("* " + str(algorithm))
    print("```")

    print("#### Features (%i)" % INPUT_FEATURES)
    print("```")
    for algorithm in feature_list:
        print("* %s" % str(algorithm))
    print("```")
    logging.info("## Start creating pfiles")

    # Traindata has to come first because of feature normalization
    for dataset_name, dataset, is_traindata in \
        [("traindata", training_set, True),
         ("testdata", test_set, False),
         ("validdata", validation_set, False)]:
        t0 = time.time()
        logging.info("Start preparing '%s' ..." % dataset_name)
        prepared, translation = prepare_dataset(dataset,
                                                formula_id2index,
                                                feature_list,
                                                is_traindata)
        logging.info("%s length: %i", dataset_name, len(prepared))
        logging.info("start 'make_pfile' ...")
        make_pfile(dataset_name,
                   INPUT_FEATURES,
                   prepared,
                   os.path.join(feature_folder, target_paths[dataset_name]),
                   create_learning_curve)
        translationfilename = "%s/translation-%s.csv" % (feature_folder,
                                                         dataset_name)
        with open(translationfilename, "w") as f:
            f.write("index,raw_data_id,latex,formula_id\n")
            for el in translation:
                f.write("%i,%i,%s,%i\n" % (formula_id2index[el[2]],
                                           el[0], el[1], el[2]))
        t1 = time.time() - t0
        logging.info("%s was written. Needed %0.2f seconds" %
                     (dataset_name, t1))
        gc.collect()
    utils.create_run_logfile(feature_folder)


def training_set_multiplication(training_set, mult_queue):
    """ Multiply the training set by all methods listed in mult_queue.
    :param training_set: set of all recordings that will be used for training
    :param mult_queue: list of all algorithms that will take one recording and
                      generate more than one.
    :returns: mutliple recordings
    """
    logging.info("Multiply data...")
    for algorithm in mult_queue:
        new_trning_set = []
        for recording in training_set:
            samples = algorithm(recording['handwriting'])
            for sample in samples:
                new_trning_set.append({'id': recording['id'],
                                       'is_in_testset': 0,
                                       'formula_id': recording['formula_id'],
                                       'handwriting': sample,
                                       'formula_in_latex':
                                       recording['formula_in_latex']})
        training_set = new_trning_set
    return new_trning_set


def get_sets(path_to_data):
    """Get a training, validation and a testset as well as a dictionary that
    maps each formula_id to an index (0...nr_of_formulas).

    :param path_to_data: a pickle file that contains a list of datasets.
    """
    loaded = pickle.load(open(path_to_data))
    datasets = loaded['handwriting_datasets']

    training_set, validation_set, test_set = [], [], []

    dataset_by_formula_id = {}
    formula_id2index = {}
    index2latex = {}

    # Group data in dataset_by_formula_id so that 10% can be used for the
    # validation set
    for i, dataset in enumerate(datasets):
        if dataset['formula_id'] in dataset_by_formula_id:
            dataset_by_formula_id[dataset['formula_id']].append(dataset)
        else:
            dataset_by_formula_id[dataset['formula_id']] = [dataset]
        utils.print_status(len(datasets), i)
    print("")

    # Create the test-, validation- and training set
    print("Create the test-, validation- and training set")
    for formula_id, dataset in dataset_by_formula_id.items():
        tmp = dataset[0]['handwriting'].formula_in_latex
        index2latex[len(formula_id2index)] = tmp
        formula_id2index[formula_id] = len(formula_id2index)
        i = 0
        for raw_data in dataset:
            if raw_data['is_in_testset']:
                test_set.append(raw_data)
            else:
                if i % 10 == 0:
                    validation_set.append(raw_data)
                else:
                    training_set.append(raw_data)
                i = (i + 1) % 10
    if 'preprocessing_queue' in loaded:
        preprocessing_queue = loaded['preprocessing_queue']
    else:
        preprocessing_queue = []
    return (training_set, validation_set, test_set, formula_id2index,
            preprocessing_queue, index2latex)


def prepare_dataset(dataset, formula_id2index, feature_list, is_traindata):
    """Transform each instance of dataset to a (Features, Label) tuple."""
    prepared = []
    start_time = time.time()
    translation = []
    for i, data in enumerate(dataset):
        x = []
        handwriting = data['handwriting']
        x = handwriting.feature_extraction(feature_list)  # Feature selection
        y = formula_id2index[data['formula_id']]  # Get label
        translation.append((handwriting.raw_data_id,
                            handwriting.formula_in_latex,
                            handwriting.formula_id))
        prepared.append((numpy.array(x), y))
        if i % 100 == 0 and i > 0:
            utils.print_status(len(dataset), i, start_time)
    sys.stdout.write("\r100%" + " "*80 + "\n")
    sys.stdout.flush()

    # Feature normalization
    if False:
        if is_traindata:
            # Create feature only list
            feats = []
            for x, y in prepared:
                feats.append(x)
            # Calculate all means / mins / maxs
            means = numpy.mean(feats, 0)
            mins = numpy.min(feats, 0)
            maxs = numpy.max(feats, 0)
            # Calculate, min, max and mean vector for each feature with
            # normalization
            start = 0
            with open("featurenormalization.csv", 'wb') as csvfile:
                spamwriter = csv.writer(csvfile, delimiter=';',
                                        quotechar='"', quoting=csv.QUOTE_MINIMAL)
                for feature in feature_list:
                    end = start + feature.get_dimension()
                    # append the data to the feature class
                    feature.mean = numpy.array(means[start:end])
                    feature.min = numpy.array(mins[start:end])
                    feature.max = numpy.array(maxs[start:end])
                    start = end
                    for mean, fmax, fmin in zip(feature.mean, feature.max,
                                                feature.min):
                        spamwriter.writerow([mean, fmax - fmin])
        start = 0
        for feature in feature_list:
            end = start + feature.get_dimension()
            # TODO: Should I check if feature normalization is activated?
            if False:  # Deactivate feature normalization due to bug
                # For every instance in the dataset: Normalize!
                for i in range(len(prepared)):
                    # The 0 is necessary as every element is (x, y)
                    feature_range = (feature.max - feature.min)
                    prepared[i][0][start:end] = (prepared[i][0][start:end] -
                                                 feature.mean) / feature_range
                start = end
    return (prepared, translation)


def make_pfile(dataset_name, feature_count, data,
               output_filename, create_learning_curve):
    """ Create the pfile.
    :param filename: name of the file that pfile_create will use to create the
                     pfile.
    :param feature_count: integer, number of features
    :type feature_count: integer
    :param data: data format ('feature_string', 'label')
    :type data: list of tuples
    """
    input_filename = os.path.abspath("%s.raw" % dataset_name)
    logging.info("Temporary file: '%s'", input_filename)
    # create raw data file for pfile_create
    if dataset_name == "traindata" and create_learning_curve:
        max_trainingexamples = 501
        output_filename_save = output_filename
        steps = 10
        for trainingexamples in range(100, max_trainingexamples, steps):
            # adjust output_filename
            tmp = output_filename_save.split(".")
            tmp[-2] += "-%i-examples" % trainingexamples
            output_filename = ".".join(map(str, tmp))
            # Count what has been written so far
            seen_symbols = defaultdict(int)
            with open(input_filename, "w") as f:
                symbolnr = 0
                for instance in data:
                    feature_string, label = instance
                    if seen_symbols[label] >= trainingexamples:
                        continue
                    seen_symbols[label] += 1
                    assert len(feature_string) == feature_count, \
                        "Expected %i features, got %i features" % \
                        (feature_count, len(feature_string))
                    feature_string = " ".join(map(str, feature_string))
                    line = "%i 0 %s %i" % (symbolnr, feature_string, label)
                    print(line, file=f)
                    symbolnr += 1
            command = "pfile_create -i %s -f %i -l 1 -o %s" % \
                      (input_filename, feature_count, output_filename)
            logging.info(command)
            os.system(command)
    else:
        with open(input_filename, "w") as f:
            for symbolnr, instance in enumerate(data):
                feature_string, label = instance
                assert len(feature_string) == feature_count, \
                    "Expected %i features, got %i features" % \
                    (feature_count, len(feature_string))
                feature_string = " ".join(map(str, feature_string))
                line = "%i 0 %s %i" % (symbolnr, feature_string, label)
                print(line, file=f)
        command = "pfile_create -i %s -f %i -l 1 -o %s" % \
                  (input_filename, feature_count, output_filename)
        logging.info(command)
        os.system(command)
        #os.remove(input_filename)


if __name__ == '__main__':
    PROJECT_ROOT = utils.get_project_root()

    # Get latest model description file
    feature_folder = os.path.join(PROJECT_ROOT, "feature-files")
    latest_featurefolder = utils.get_latest_folder(feature_folder)

    # Get command line arguments
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-f", "--folder",
                        dest="folder",
                        help="where is the feature file folder "
                             "(that contains a info.yml)?",
                        metavar="FOLDER",
                        type=lambda x: utils.is_valid_folder(parser, x),
                        default=latest_featurefolder)
    parser.add_argument("-l", "--learning-curve",
                        dest="create_learning_curve",
                        help="create pfiles for a learning curve",
                        action='store_true',
                        default=False)
    args = parser.parse_args()

    main(args.folder, args.create_learning_curve)
