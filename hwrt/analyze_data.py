#!/usr/bin/env python

"""
Analyze data in a pickle file by maximum time / width / height and
similar features.
"""


# Core Library modules
import logging
import pickle
import sys

# Third party modules
import numpy

# Local modules
from . import data_analyzation_metrics as dam
from . import features, handwritten_data, utils

logger = logging.getLogger(__name__)
sys.modules["hwrt.HandwrittenData"] = handwritten_data


def filter_label(label, replace_by_similar=True):
    """Some labels currently don't work together because of LaTeX naming
       clashes. Those will be replaced by simple strings. """
    bad_names = [
        "celsius",
        "degree",
        "ohm",
        "venus",
        "mars",
        "astrosun",
        "fullmoon",
        "leftmoon",
        "female",
        "male",
        "checked",
        "diameter",
        "sun",
        "Bowtie",
        "sqrt",
        "cong",
        "copyright",
        "dag",
        "parr",
        "notin",
        "dotsc",
        "mathds",
        "mathfrak",
    ]
    if any(label[1:].startswith(bad) for bad in bad_names):
        if label == "\\dag" and replace_by_similar:
            return "\\dagger"
        elif label == "\\diameter" and replace_by_similar:
            return "\\O"
        return label[1:]
    else:
        return label


def analyze_feature(raw_datasets, feature, basename="aspect_ratios"):
    """
    Apply ``feature`` to all recordings in ``raw_datasets``. Store the results
    in two files. One file stores the raw result, the other one groups the
    results by symbols and stores the mean, standard deviation and the name of
    the symbol as a csv file.

    Parameters
    ----------
    raw_datasets : List of dictionaries
        Each dictionary is a raw_dataset.
    feature : An instance of the feature class type
        The `feature` which gets analyzed on `raw_datasets`.
    basename : string
        Name for the file in which the data gets written.
    """

    # Prepare files
    csv_file = dam.prepare_file(basename + ".csv")
    raw_file = dam.prepare_file(basename + ".raw")

    csv_file = open(csv_file, "a")
    raw_file = open(raw_file, "a")

    csv_file.write("label,mean,std\n")  # Write header
    raw_file.write("latex,raw_data_id,value\n")  # Write header

    print_data = []
    for _, datasets in dam.sort_by_formula_id(raw_datasets).items():
        values = []
        for data in datasets:
            value = feature(data)[0]
            values.append(value)
            raw_file.write(
                "%s,%i,%0.2f\n"
                % (datasets[0].formula_in_latex, data.raw_data_id, value)
            )
        label = filter_label(datasets[0].formula_in_latex)
        print_data.append((label, numpy.mean(values), numpy.std(values)))

    # Sort the data by highest mean, descending
    print_data = sorted(print_data, key=lambda n: n[1], reverse=True)

    # Write data to file
    for label, mean, std in print_data:
        csv_file.write(f"{label},{mean:0.2f},{std:0.2f}\n")
    csv_file.close()


def main(handwriting_datasets_file, analyze_features):
    """Start the creation of the wanted metric."""
    # Load from pickled file
    logger.info(f"Start loading data '{handwriting_datasets_file}' ...")
    with open(handwriting_datasets_file, "rb") as f:
        loaded = pickle.load(f)
    raw_datasets = loaded["handwriting_datasets"]
    logger.info(f"{len(raw_datasets)} datasets loaded.")
    logger.info("Start analyzing...")

    if analyze_features:
        featurelist = [
            (features.AspectRatio(), "aspect_ratio.csv"),
            (features.ReCurvature(1), "re_curvature.csv"),
            (features.Height(), "height.csv"),
            (features.Width(), "width.csv"),
            (features.Time(), "time.csv"),
            (features.Ink(), "ink.csv"),
            (features.StrokeCount(), "stroke-count.csv"),
        ]
        for feat, filename in featurelist:
            logger.info("create %s...", filename)
            analyze_feature(raw_datasets, feat, filename)

    # Analyze everything specified in configuration
    cfg = utils.get_project_configuration()
    if "data_analyzation_queue" in cfg:
        metrics = dam.get_metrics(cfg["data_analyzation_queue"])
        for metric in metrics:
            logger.info("Start metric %s...", str(metric))
            metric(raw_datasets)
    else:
        logger.info("No 'data_analyzation_queue' in ~/.hwrtrc")
