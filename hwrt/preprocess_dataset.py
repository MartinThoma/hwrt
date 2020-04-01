#!/usr/bin/env python

"""Create preprocessed dataset."""


# Core Library modules
import logging
import os
import pickle
import sys
import time

# Third party modules
import yaml

# Local modules
from . import handwritten_data, preprocessing, utils

logger = logging.getLogger(__name__)
sys.modules["hwrt.HandwrittenData"] = handwritten_data
sys.modules["HandwrittenData"] = handwritten_data


def get_parameters(folder):
    """Get the parameters of the preprocessing done within `folder`.

    Parameters
    ----------
    folder : string

    Returns
    -------
    tuple : (path of raw data,
             path where preprocessed data gets stored,
             list of preprocessing algorithms)
    """

    # Read the model description file
    with open(os.path.join(folder, "info.yml")) as ymlfile:
        preprocessing_description = yaml.safe_load(ymlfile)

    # Get the path of the raw data
    raw_datapath = os.path.join(
        utils.get_project_root(), preprocessing_description["data-source"]
    )
    # Get the path were the preprocessed file should be put
    outputpath = os.path.join(folder, "data.pickle")

    # Get the preprocessing queue
    tmp = preprocessing_description["queue"]
    preprocessing_queue = preprocessing.get_preprocessing_queue(tmp)
    return (raw_datapath, outputpath, preprocessing_queue)


def create_preprocessed_dataset(path_to_data, outputpath, preprocessing_queue):
    """Create a preprocessed dataset file by applying `preprocessing_queue`
       to `path_to_data`. The result will be stored in `outputpath`."""
    # Log everything
    logger.info("Data soure %s", path_to_data)
    logger.info("Output will be stored in %s", outputpath)
    tmp = "Preprocessing Queue:\n"
    for preprocessing_class in preprocessing_queue:
        tmp += str(preprocessing_class) + "\n"
    logger.info(tmp)
    # Load from pickled file
    if not os.path.isfile(path_to_data):
        logger.info(
            (
                "'%s' does not exist. Please either abort this script "
                "or update the data location."
            ),
            path_to_data,
        )
        raw_dataset_path = utils.choose_raw_dataset()
        # Get project-relative path
        raw_dataset_path = "raw-datasets" + raw_dataset_path.split("raw-datasets")[1]
        print(raw_dataset_path)
        sys.exit()  # TODO: Update model!
    logger.info("Start loading data...")
    loaded = pickle.load(open(path_to_data, "rb"))
    raw_datasets = loaded["handwriting_datasets"]
    logger.info("Start applying preprocessing methods")
    start_time = time.time()
    for i, raw_dataset in enumerate(raw_datasets):
        if i % 10 == 0 and i > 0:
            utils.print_status(len(raw_datasets), i, start_time)
        # Do the work
        raw_dataset["handwriting"].preprocessing(preprocessing_queue)
    sys.stdout.write("\r%0.2f%% (done)\033[K\n" % (100))
    print("")
    pickle.dump(
        {
            "handwriting_datasets": raw_datasets,
            "formula_id2latex": loaded["formula_id2latex"],
            "preprocessing_queue": preprocessing_queue,
        },
        open(outputpath, "wb"),
        2,
    )


def main(folder):
    """Main part of preprocess_dataset that glues things togeter."""
    raw_datapath, outputpath, p_queue = get_parameters(folder)
    create_preprocessed_dataset(raw_datapath, outputpath, p_queue)
    utils.create_run_logfile(folder)
