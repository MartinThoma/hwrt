#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Create and train a given model."""

import logging
import sys
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)
import os
import yaml
import datetime

# hwrt modules
import hwrt.utils as utils
import hwrt.preprocess_dataset as preprocess_dataset
import hwrt.create_pfiles as create_pfiles
import hwrt.create_model as create_model


def update_if_outdated(folder):
    """Check if the currently watched instance (model, feature or
        preprocessing) is outdated and update it eventually.
    """

    folders = []
    while os.path.isdir(folder):
        folders.append(folder)
        # Get info.yml
        with open(os.path.join(folder, "info.yml")) as ymlfile:
            content = yaml.load(ymlfile)
        folder = os.path.join(utils.get_project_root(), content['data-source'])
    raw_source_file = folder
    if not os.path.isfile(raw_source_file):
        logging.error("File '%s' was not found.", raw_source_file)
        logging.error("You should eventually execute 'hwrt download'.")
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
                logging.info("Preprocessed file was outdated. Update...")
                preprocess_dataset.main(os.path.join(utils.get_project_root(),
                                                     target_folder))
            elif "feature-files" in target_folder:
                logging.info("Feature file was outdated. Update...")
                create_pfiles.main(target_folder)
            elif "model" in target_folder:
                logging.info("Model file was outdated. Update...")
                create_model.main(target_folder, True)
            target_mtime = datetime.datetime.utcnow()
        else:
            logging.info("'%s' is up-to-date.", target_folder)
        source_mtime = target_mtime


def generate_training_command(model_folder):
    """Generate a string that contains a command with all necessary
       parameters to train the model."""
    update_if_outdated(model_folder)
    model_description_file = os.path.join(model_folder, "info.yml")
    # Read the model description file
    with open(model_description_file, 'r') as ymlfile:
        model_description = yaml.load(ymlfile)

    # Get the data paths (pfiles)
    project_root = utils.get_project_root()
    data = {}
    data['training'] = os.path.join(project_root,
                                    model_description["data-source"],
                                    "traindata.pfile")
    data['testing'] = os.path.join(project_root,
                                   model_description["data-source"],
                                   "testdata.pfile")
    data['validating'] = os.path.join(project_root,
                                      model_description["data-source"],
                                      "validdata.pfile")

    # Get latest model file
    basename = "model"
    latest_model = utils.get_latest_working_model(model_folder)

    if latest_model == "":
        logging.error("There is no model with basename '%s'.", basename)
        return None
    else:
        logging.info("Model '%s' found.", latest_model)
        i = int(latest_model.split("-")[-1].split(".")[0])
        model_src = os.path.join(model_folder, "%s-%i.json" % (basename, i))
        model_target = os.path.join(model_folder,
                                    "%s-%i.json" % (basename, i+1))

    # generate the training command
    training = model_description['training']
    training = training.replace("{{testing}}", data['testing'])
    training = training.replace("{{training}}", data['training'])
    training = training.replace("{{validation}}", data['validating'])
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
    logging.info(training)
    os.chdir(model_folder)
    os.system(training)


def main(model_folder):
    """Main part of the training script."""
    model_description_file = os.path.join(model_folder, "info.yml")

    # Read the model description file
    with open(model_description_file, 'r') as ymlfile:
        model_description = yaml.load(ymlfile)

    # Analyze model
    logging.info(model_description['model'])
    data = {}
    data['training'] = os.path.join(model_folder, "traindata.pfile")
    data['testing'] = os.path.join(model_folder, "testdata.pfile")
    data['validating'] = os.path.join(model_folder, "validdata.pfile")
    train_model(model_folder)


def get_parser():
    """Return the parser object for this script."""
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-m", "--model",
                        dest="model",
                        help="where is the model folder (with a info.yml)?",
                        metavar="FOLDER",
                        type=lambda x: utils.is_valid_folder(parser, x),
                        default=utils.default_model())
    return parser

if __name__ == "__main__":
    args = get_parser().parse_args()
    main(args.model)
