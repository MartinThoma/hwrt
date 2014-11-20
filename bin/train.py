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

# hwrt modules
import hwrt.utils as utils


def generate_training_command(model_folder):
    """Generate a string that contains a command with all necessary
       parameters to train the model."""
    utils.update_if_outdated(model_folder)
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


def train_model(model_folder, model_description, data):
    """Train the model in ``model_folder``.
    :param data: The information where the data (pfiles) is.
    :type data: dictionary"""
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
    train_model(model_folder, model_description, data)


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
