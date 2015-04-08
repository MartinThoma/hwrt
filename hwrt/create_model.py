#!/usr/bin/env python

"""Create a model."""

import logging
import os
import yaml

# hwrt modules
from . import utils
from . import features


def create_model(model_folder, model_type, topology, override):
    """
    Create a model if it doesn't exist already.

    Parameters
    ----------
    model_folder :
        The path to the folder where the model is described with an `info.yml`
    model_type :
        MLP
    topology :
        Something like 160:500:369 - that means the first layer has 160
        neurons, the second layer has 500 neurons and the last layer has 369
        neurons.
    override : boolean
        If a model exists, override it.
    """
    latest_model = utils.get_latest_in_folder(model_folder, ".json")
    if (latest_model == "") or override:
        logging.info("Create a base model...")
        model_src = os.path.join(model_folder, "model-0.json")
        command = "%s make %s %s > %s" % (utils.get_nntoolkit(),
                                          model_type,
                                          topology,
                                          model_src)
        logging.info(command)
        os.system(command)
    else:
        logging.info("Model file already existed.")


def main(model_folder, override=False):
    """Parse the info.yml from ``model_folder`` and create the model file."""
    model_description_file = os.path.join(model_folder, "info.yml")
    # Read the model description file
    with open(model_description_file, 'r') as ymlfile:
        model_description = yaml.load(ymlfile)

    project_root = utils.get_project_root()
    # Read the feature description file
    feature_folder = os.path.join(project_root,
                                  model_description['data-source'])
    with open(os.path.join(feature_folder, "info.yml"), 'r') as ymlfile:
        feature_description = yaml.load(ymlfile)
    # Get a list of all used features
    feature_list = features.get_features(feature_description['features'])
    # Get the dimension of the feature vector
    input_features = sum(map(lambda n: n.get_dimension(), feature_list))
    logging.info("Number of features: %i", input_features)

    # Analyze model
    logging.info(model_description['model'])
    if model_description['model']['type'] != 'mlp':
        return
    create_model(model_folder,
                 model_description['model']['type'],
                 model_description['model']['topology'],
                 override)
    utils.create_run_logfile(model_folder)


def get_parser():
    """Return the parser object for this script."""
    project_root = utils.get_project_root()

    # Get latest model folder
    models_folder = os.path.join(project_root, "models")
    latest_model = utils.get_latest_folder(models_folder)

    # Get command line arguments
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-m", "--model",
                        dest="model",
                        help="where is the model folder (with a info.yml)?",
                        metavar="FOLDER",
                        type=lambda x: utils.is_valid_folder(parser, x),
                        default=latest_model)
    parser.add_argument("-o", "--override",
                        action="store_true", dest="override",
                        default=False,
                        help=("should the model be overridden "
                              "if it already exists?"))
    return parser


if __name__ == "__main__":
    args = get_parser().parse_args()
    main(args.model, args.override)
