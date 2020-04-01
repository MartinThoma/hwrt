#!/usr/bin/env python

"""Create a model."""

# Core Library modules
import logging
import os

# Third party modules
import yaml

# Local modules
from . import features, utils

logger = logging.getLogger(__name__)


def create_model(model_folder: str, model_type: str, topology: str, override: bool):
    """
    Create a model if it doesn't exist already.

    Parameters
    ----------
    model_folder : str
        The path to the folder where the model is described with an `info.yml`
    model_type : {'MLP'}
        MLP
    topology : str
        Something like 160:500:369 - that means the first layer has 160
        neurons, the second layer has 500 neurons and the last layer has 369
        neurons.
    override : bool
        If a model exists, override it.
    """
    latest_model = utils.get_latest_in_folder(model_folder, ".json")
    if (latest_model == "") or override:
        logger.info("Create a base model...")
        model_src = os.path.join(model_folder, "model-0.json")
        command = (
            f"{utils.get_nntoolkit()} create {model_type} {topology} " f"> {model_src}"
        )
        logger.info(command)
        os.system(command)
    else:
        logger.info("Model file already existed.")


def main(model_folder, override=False):
    """Parse the info.yml from ``model_folder`` and create the model file."""
    model_description_file = os.path.join(model_folder, "info.yml")
    # Read the model description file
    with open(model_description_file) as ymlfile:
        model_description = yaml.safe_load(ymlfile)

    project_root = utils.get_project_root()
    # Read the feature description file
    feature_folder = os.path.join(project_root, model_description["data-source"])
    with open(os.path.join(feature_folder, "info.yml")) as ymlfile:
        feature_description = yaml.safe_load(ymlfile)
    # Get a list of all used features
    feature_list = features.get_features(feature_description["features"])
    # Get the dimension of the feature vector
    input_features = sum([n.get_dimension() for n in feature_list])
    logger.info("Number of features: %i", input_features)

    # Analyze model
    logger.info(model_description["model"])
    if model_description["model"]["type"] != "mlp":
        return
    create_model(
        model_folder,
        model_description["model"]["type"],
        model_description["model"]["topology"],
        override,
    )
    utils.create_run_logfile(model_folder)
