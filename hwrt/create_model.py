#!/usr/bin/env python

"""Create a model."""

import os
import yaml
import logging
import sys
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)
# mine
import utils
import features


def create_model(model_folder, model_type, topology, override):
    latest_model = utils.get_latest_in_folder(model_folder, ".json")
    if (latest_model == "") or override:
        logging.info("Create a base model...")
        model_src = os.path.join(model_folder, "model-0.json")
        command = "nntoolkit make %s %s > %s" % (model_type,
                                                 topology,
                                                 model_src)
        logging.info(command)
        os.system(command)
    else:
        logging.info("Model file already existed.")


def main(model_folder, override=False):
    # That would cause an infinite loop:
    # utils.update_if_outdated(model_folder)
    model_description_file = os.path.join(model_folder, "info.yml")
    # Read the model description file
    with open(model_description_file, 'r') as ymlfile:
        model_description = yaml.load(ymlfile)

    PROJECT_ROOT = utils.get_project_root()
    # Read the feature description file
    feature_folder = os.path.join(PROJECT_ROOT,
                                  model_description['data-source'])
    with open(os.path.join(feature_folder, "info.yml"), 'r') as ymlfile:
        feature_description = yaml.load(ymlfile)
    # Get a list of all used features
    feature_list = features.get_features(feature_description['features'])
    # Get the dimension of the feature vector
    INPUT_FEATURES = sum(map(lambda n: n.get_dimension(), feature_list))
    logging.info("Number of features: %i" % INPUT_FEATURES)

    # Analyze model
    logging.info(model_description['model'])
    if model_description['model']['type'] != 'mlp':
        return
    create_model(model_folder,
                 model_description['model']['type'],
                 model_description['model']['topology'],
                 override)
    utils.create_run_logfile(model_folder)


if __name__ == "__main__":
    PROJECT_ROOT = utils.get_project_root()

    # Get latest model folder
    models_folder = os.path.join(PROJECT_ROOT, "archive/models")
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
    args = parser.parse_args()
    main(args.model, args.override)
