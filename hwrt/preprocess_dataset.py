#!/usr/bin/env python

"""Create preprocessed dataset."""

from __future__ import print_function
import logging
import sys
import os
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)
import cPickle as pickle
import time
import preprocessing
import yaml
import utils


def main(folder):
    raw_datapath, outputpath, p_queue = get_parameters(folder)
    create_preprocessed_dataset(raw_datapath, outputpath, p_queue)
    utils.create_run_logfile(folder)


def get_parameters(folder):
    PROJECT_ROOT = utils.get_project_root()
    # Read the model description file
    with open(os.path.join(folder, "info.yml"), 'r') as ymlfile:
        preprocessing_description = yaml.load(ymlfile)

    # Get the path of the raw data
    raw_datapath = os.path.join(PROJECT_ROOT,
                                preprocessing_description['data-source'])
    # Get the path were the preprocessed file should be put
    outputpath = os.path.join(folder, "data.pickle")

    # Get the preprocessing queue
    tmp = preprocessing_description['queue']
    preprocessing_queue = preprocessing.get_preprocessing_queue(tmp)
    return (raw_datapath, outputpath, preprocessing_queue)


def create_preprocessed_dataset(path_to_data, outputpath, preprocessing_queue):
    # Log everything
    logging.info("Data soure %s" % path_to_data)
    logging.info("Output will be stored in %s" % outputpath)
    tmp = "Preprocessing Queue:\n"
    for el in preprocessing_queue:
        tmp += str(el) + "\n"
    logging.info(tmp)
    # Load from pickled file
    if not os.path.isfile(path_to_data):
        logging.info(("'%s' does not exist. Please either abort this script "
                      "or update the data location."), path_to_data)
        raw_dataset_path = utils.choose_raw_dataset()
        # Get project-relative path
        raw_dataset_path = "archive/raw-datasets" + \
                           raw_dataset_path.split("archive/raw-datasets")[1]
        print(raw_dataset_path)
        sys.exit()  # TODO: Update model!
    logging.info("Start loading data...")
    loaded = pickle.load(open(path_to_data))
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
                 'preprocessing_queue': preprocessing_queue
                 },
                open(outputpath, "wb"),
                2)


if __name__ == '__main__':
    PROJECT_ROOT = utils.get_project_root()

    # Get latest model description file
    preprocessed_folder = os.path.join(PROJECT_ROOT, "archive/preprocessed")
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
