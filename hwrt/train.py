#!/usr/bin/env python

"""Create and train a given model."""

# Core Library modules
import datetime
import logging
import os
import sys

# Third party modules
import yaml

# First party modules
import hwrt.create_ffiles as create_ffiles
import hwrt.create_model as create_model
import hwrt.preprocess_dataset as preprocess_dataset
import hwrt.utils as utils

logger = logging.getLogger(__name__)


def update_if_outdated(folder):
    """Check if the currently watched instance (model, feature or
        preprocessing) is outdated and update it eventually.
    """

    folders = []
    while os.path.isdir(folder):
        folders.append(folder)
        # Get info.yml
        with open(os.path.join(folder, "info.yml")) as ymlfile:
            content = yaml.safe_load(ymlfile)
        folder = os.path.join(utils.get_project_root(), content["data-source"])
    raw_source_file = folder
    if not os.path.isfile(raw_source_file):
        logger.error("File '%s' was not found.", raw_source_file)
        logger.error("You should eventually execute 'hwrt download'.")
        sys.exit(-1)
    dt = os.path.getmtime(raw_source_file)
    source_mtime = datetime.datetime.utcfromtimestamp(dt)
    folders = folders[::-1]  # Reverse order to get the most "basic one first"

    for target_folder in folders:
        target_mtime = utils.get_latest_successful_run(target_folder)
        if target_mtime is None or source_mtime > target_mtime:
            # The source is later than the target. That means we need to
            # refresh the target
            if "preprocessed" in target_folder:
                logger.info("Preprocessed file was outdated. Update...")
                preprocess_dataset.main(
                    os.path.join(utils.get_project_root(), target_folder)
                )
            elif "feature-files" in target_folder:
                logger.info("Feature file was outdated. Update...")
                create_ffiles.main(target_folder)
            elif "model" in target_folder:
                logger.info("Model file was outdated. Update...")
                create_model.main(target_folder, True)
            target_mtime = datetime.datetime.utcnow()
        else:
            logger.info(f"'{target_folder}' is up-to-date.")
        source_mtime = target_mtime


def generate_training_command(model_folder):
    """Generate a string that contains a command with all necessary
       parameters to train the model."""
    update_if_outdated(model_folder)
    model_description_file = os.path.join(model_folder, "info.yml")
    # Read the model description file
    with open(model_description_file) as ymlfile:
        model_description = yaml.safe_load(ymlfile)

    # Get the data paths (hdf5 files)
    project_root = utils.get_project_root()
    data = {}
    data["training"] = os.path.join(
        project_root, model_description["data-source"], "traindata.hdf5"
    )
    data["testing"] = os.path.join(
        project_root, model_description["data-source"], "testdata.hdf5"
    )
    data["validating"] = os.path.join(
        project_root, model_description["data-source"], "validdata.hdf5"
    )

    # Get latest model file
    basename = "model"
    latest_model = utils.get_latest_working_model(model_folder)

    if latest_model == "":
        logger.error(
            f"There is no model with basename '{basename}' " f"in {model_folder}"
        )
        return None
    else:
        logger.info(f"Model '{latest_model}' found.")
        i = int(latest_model.split("-")[-1].split(".")[0])
        model_src = os.path.join(model_folder, f"{basename}-{i}.json")
        model_target = os.path.join(model_folder, f"{basename}-{i + 1}.json")

    # generate the training command
    training = model_description["training"]
    training = training.replace("{{testing}}", data["testing"])
    training = training.replace("{{training}}", data["training"])
    training = training.replace("{{validation}}", data["validating"])
    training = training.replace("{{src_model}}", model_src)
    training = training.replace("{{target_model}}", model_target)
    training = training.replace("{{nntoolkit}}", utils.get_nntoolkit())
    return training


def train_model(model_folder):
    """Train the model in ``model_folder``."""
    os.chdir(model_folder)
    training = generate_training_command(model_folder)
    if training is None:
        return -1
    logger.info(training)
    os.chdir(model_folder)
    os.system(training)


def main(model_folder):
    """Main part of the training script."""
    model_description_file = os.path.join(model_folder, "info.yml")

    # Read the model description file
    with open(model_description_file) as ymlfile:
        model_description = yaml.safe_load(ymlfile)

    # Analyze model
    logger.info(model_description["model"])
    data = {}
    data["training"] = os.path.join(model_folder, "traindata.hdf5")
    data["testing"] = os.path.join(model_folder, "testdata.hdf5")
    data["validating"] = os.path.join(model_folder, "validdata.hdf5")
    train_model(model_folder)
