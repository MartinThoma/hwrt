#!/usr/bin/env python

"""
hwrt, the handwriting recognition toolkit, is a set of executable scripts
and Python modules that are useful for handwriting recognition.

For train.py, test.py you will need an internal toolkit for training of
neural networks. The backup.py script is only useful if you have a
website like write-math.com to collect recordings.
"""
# Core Library modules
import logging
import os
import sys

# Third party modules
import click

# First party modules
import hwrt
import hwrt.utils

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.DEBUG,
    stream=sys.stdout,
)


@click.group()
@click.version_option(version=hwrt.__version__)
def entry_point():
    pass


model_option = click.option(
    "-m",
    "--model",
    default=hwrt.utils.default_model(),
    show_default=True,
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    help="where is the model folder (with a info.yml)?",
)


@entry_point.command()
def selfcheck():
    """Self-check of the HWRT toolkit."""
    import hwrt.selfcheck

    hwrt.selfcheck.main()


@entry_point.command()
@click.option(
    "-i", "--id", "raw_data_id", default=292293, type=int,
)
@click.option(
    "--mysql",
    "mysql_cfg",
    default="mysql_online",
    type=str,
    help="which mysql configuration should be used?",
)
@model_option
@click.option(
    "-l",
    "--list",
    "list_ids",
    default=False,
    help="list all raw data IDs / symbol IDs",
    is_flag=True,
)
@click.option(
    "-s",
    "--server",
    "contact_server",
    default=False,
    help="contact the MySQL server",
    is_flag=True,
)
@click.option(
    "-r",
    "--raw",
    "show_raw",
    default=False,
    help="show the raw recording (without preprocessing)",
    is_flag=True,
)
def view(raw_data_id, mysql_cfg, model, list_ids, contact_server, show_raw):
    """Display raw preprocessed recordings."""
    import hwrt.view

    hwrt.view.main(
        list_ids=list_ids,
        model=model,
        contact_server=contact_server,
        raw_data_id=raw_data_id,
        show_raw=show_raw,
        mysql_cfg=mysql_cfg,
    )


@entry_point.command()
def download():
    """Download the raw data to start analyzation / traning."""
    import hwrt.download

    hwrt.download.main()


@entry_point.command()
@model_option
@click.option(
    "-s",
    "--set",
    "aset",
    type=click.Choice(["test", "train", "valid"]),
    default="test",
    help="which set should get analyzed?",
)
@click.option(
    "-n", type=int, default=1, help="Top-N error",
)
@click.option(
    "--merge",
    default=False,
    help="merge problem classes that are easy to confuse",
    is_flag=True,
)
def test(model, aset, n, merge):
    """Test a given model against a dataset."""
    import hwrt.test

    hwrt.test.main(model, aset, n, merge)


project_root = hwrt.utils.get_project_root()
dataset_folder = os.path.join(project_root, "raw-datasets")
latest_dataset = hwrt.utils.get_latest_in_folder(dataset_folder, "raw.pickle")


@entry_point.command()
@click.option(
    "-d",
    "--handwriting_datasets",
    type=click.Path(dir_okay=False, file_okay=True, exists=True),
    default=latest_dataset,
    help="where are the pickled handwriting_datasets?",
)
@click.option(
    "-f",
    "--features",
    "analyze_features",
    default=False,
    help="merge problem classes that are easy to confuse",
    is_flag=True,
)
def analyze_data(handwriting_datasets, analyze_features):
    """Analyze data according to many metrics."""
    import hwrt.analyze_data

    hwrt.analyze_data.main(handwriting_datasets, analyze_features)


@entry_point.command()
@model_option
def train(model):
    """Train a model."""
    import hwrt.train

    hwrt.train.main(model)


# Get latest model description file
feature_folder = os.path.join(project_root, "feature-files")
latest_featurefolder = hwrt.utils.get_latest_folder(feature_folder)


@entry_point.command()
@click.option(
    "-l",
    "--learning-curve",
    "create_learning_curve",
    default=False,
    help="create hdf5 files for a learning curve",
    is_flag=True,
)
@click.option(
    "-f",
    "--folder",
    default=latest_featurefolder,
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    help="where is the feature file folder (that contains a info.yml)?",
)
def create_ffiles(folder, create_learning_curve):
    """A tool to create compressed feature files from preprocessed files."""
    import hwrt.create_ffiles

    hwrt.create_ffiles.main(folder, create_learning_curve)


# Get latest model folder
models_folder = os.path.join(project_root, "models")
latest_model = hwrt.utils.get_latest_folder(models_folder)


@entry_point.command()
@click.option(
    "-m",
    "--model",
    default=latest_model,
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    help="where is the model folder (with a info.yml)?",
)
@click.option(
    "-o",
    "--override",
    default=False,
    help="should the model be overridden if it already exists?",
    is_flag=True,
)
def create_model(model, override):
    """Create a model file."""
    import hwrt.create_model

    hwrt.create_model.main(model, override)


@entry_point.command()
@click.option("--port", default=5000, type=int, help="where should the webserver run")
@click.option("-n", default=10, type=int, help="Show TOP-N results")
@click.option(
    "--use_segmenter",
    default=False,
    help="try to segment the input for multiple symbol recognition",
    is_flag=True,
)
def serve(port, n, use_segmenter):
    """Start a web-server which can classify recordings."""
    import hwrt.serve

    hwrt.serve.main(port=port, n_output=n, use_segmenter=use_segmenter)


@entry_point.command()
@click.option(
    "-s",
    "--symbol",
    "symbol_filename",
    type=click.Path(dir_okay=False, file_okay=True, exists=True),
    help="symbol yml file",
)
@click.option(
    "-r",
    "--raw",
    "raw_filename",
    type=click.Path(dir_okay=False, file_okay=True, exists=True),
    help="raw pickle file",
)
@click.option(
    "-d",
    "--dest",
    "pickle_dest_path",
    type=click.Path(dir_okay=False, file_okay=True, exists=True),
    help="pickle destination file",
)
def filter_dataset(symbol_filename, raw_filename, pickle_dest_path):
    """Filter a raw dataset."""
    import hwrt.filter_dataset

    hwrt.filter_dataset.main(symbol_filename, raw_filename, pickle_dest_path)


preprocessed_folder = os.path.join(hwrt.utils.get_project_root(), "preprocessed")
latest_preprocessed = hwrt.utils.get_latest_folder(preprocessed_folder)


@entry_point.command()
@click.option(
    "-f",
    "--folder",
    default=latest_preprocessed,
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    help="where is the feature file folder (that contains a info.yml)?",
)
def preprocess_dataset(folder):
    import hwrt.preprocess_dataset

    hwrt.preprocess_dataset.main(folder)
