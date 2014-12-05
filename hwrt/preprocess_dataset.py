#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Create preprocessed dataset."""

from __future__ import print_function
import logging
import sys
import os
import yaml
try:  # Python 2
    import cPickle as pickle
except ImportError:  # Python 3
    import pickle
import time

# hwrt modules
from . import utils
from . import preprocessing
from . import HandwrittenData

sys.modules['hwrt.HandwrittenData'] = HandwrittenData
sys.modules['HandwrittenData'] = HandwrittenData


def get_parameters(folder):
    """Get the parameters of the preprocessing done within ``folder``."""

    # Read the model description file
    with open(os.path.join(folder, "info.yml"), 'r') as ymlfile:
        preprocessing_description = yaml.load(ymlfile)

    # Get the path of the raw data
    raw_datapath = os.path.join(utils.get_project_root(),
                                preprocessing_description['data-source'])
    # Get the path were the preprocessed file should be put
    outputpath = os.path.join(folder, "data.pickle")

    # Get the preprocessing queue
    tmp = preprocessing_description['queue']
    preprocessing_queue = preprocessing.get_preprocessing_queue(tmp)
    return (raw_datapath, outputpath, preprocessing_queue)


def create_preprocessed_dataset(path_to_data, outputpath, preprocessing_queue):
    """Create a preprocessed dataset file by applying ``preprocessing_queue``
       to ``path_to_data``. The result will be stored in ``outputpath``."""
    # Log everything
    logging.info("Data soure %s", path_to_data)
    logging.info("Output will be stored in %s", outputpath)
    tmp = "Preprocessing Queue:\n"
    for preprocessing_class in preprocessing_queue:
        tmp += str(preprocessing_class) + "\n"
    logging.info(tmp)
    # Load from pickled file
    if not os.path.isfile(path_to_data):
        logging.info(("'%s' does not exist. Please either abort this script "
                      "or update the data location."), path_to_data)
        raw_dataset_path = utils.choose_raw_dataset()
        # Get project-relative path
        raw_dataset_path = "raw-datasets" + \
                           raw_dataset_path.split("raw-datasets")[1]
        print(raw_dataset_path)
        sys.exit()  # TODO: Update model!
    logging.info("Start loading data...")
    loaded = pickle.load(open(path_to_data, "rb"))
    raw_datasets = loaded['handwriting_datasets']
    logging.info("Start applying preprocessing methods")
    start_time = time.time()
    for i, raw_dataset in enumerate(raw_datasets):
        if i % 10 == 0 and i > 0:
            utils.print_status(len(raw_datasets), i, start_time)
        # Do the work
        raw_dataset['handwriting'].preprocessing(preprocessing_queue)
    sys.stdout.write("\r%0.2f%% (done)\033[K\n" % (100))
    print("")
    pickle.dump({'handwriting_datasets': raw_datasets,
                 'formula_id2latex': loaded['formula_id2latex'],
                 'preprocessing_queue': preprocessing_queue},
                open(outputpath, "wb"),
                2)


def main(folder):
    """Main part of preprocess_dataset that glues things togeter."""
    raw_datapath, outputpath, p_queue = get_parameters(folder)
    create_preprocessed_dataset(raw_datapath, outputpath, p_queue)
    utils.create_run_logfile(folder)


if __name__ == '__main__':

    # Get latest model description file
    preprocessed_folder = os.path.join(utils.get_project_root(),
                                       "preprocessed")
    latest_preprocessed = utils.get_latest_folder(preprocessed_folder)

    # Get command line arguments
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-f", "--folder",
                        dest="folder",
                        help="where is the preprocessing folder "
                             "(that contains a info.yml)?",
                        metavar="FOLDER",
                        type=lambda x: utils.is_valid_folder(parser, x),
                        default=latest_preprocessed)
    args = parser.parse_args()
    main(args.folder)
