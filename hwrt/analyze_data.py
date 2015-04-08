#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Analyze data in a pickle file by maximum time / width / height and
   similar features.
"""

from __future__ import print_function
import os
import logging
import sys
try:  # Python 2
    import cPickle as pickle
except ImportError:  # Python 3
    import pickle
import numpy

# hwrt modules
# HandwrittenData is necessary because of pickle
from hwrt import HandwrittenData
sys.modules['HandwrittenData'] = HandwrittenData
import hwrt.features as features
import hwrt.utils as utils
import hwrt.data_analyzation_metrics as dam


def filter_label(label, replace_by_similar=True):
    """Some labels currently don't work together because of LaTeX naming
       clashes. Those will be replaced by simple strings. """
    bad_names = ['celsius', 'degree', 'ohm', 'venus', 'mars', 'astrosun',
                 'fullmoon', 'leftmoon', 'female', 'male', 'checked',
                 'diameter', 'sun', 'Bowtie', 'sqrt',
                 'cong', 'copyright', 'dag', 'parr', 'notin', 'dotsc',
                 'mathds', 'mathfrak']
    if any(label[1:].startswith(bad) for bad in bad_names):
        if label == '\\dag' and replace_by_similar:
            return '\\dagger'
        elif label == '\\diameter' and replace_by_similar:
            return '\\O'
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
    csv_file = dam.prepare_file(basename+'.csv')
    raw_file = dam.prepare_file(basename+'.raw')

    csv_file = open(csv_file, 'a')
    raw_file = open(raw_file, 'a')

    csv_file.write("label,mean,std\n")  # Write header
    raw_file.write("latex,raw_data_id,value\n")  # Write header

    print_data = []
    for _, datasets in dam.sort_by_formula_id(raw_datasets).items():
        values = []
        for data in datasets:
            value = feature(data)[0]
            values.append(value)
            raw_file.write("%s,%i,%0.2f\n" % (datasets[0].formula_in_latex,
                                              data.raw_data_id,
                                              value))
        label = filter_label(datasets[0].formula_in_latex)
        print_data.append((label, numpy.mean(values), numpy.std(values)))

    # Sort the data by highest mean, descending
    print_data = sorted(print_data, key=lambda n: n[1], reverse=True)

    # Write data to file
    for label, mean, std in print_data:
        csv_file.write("%s,%0.2f,%0.2f\n" % (label, mean, std))
    csv_file.close()


def main(handwriting_datasets_file, analyze_features):
    """Start the creation of the wanted metric."""
    # Load from pickled file
    logging.info("Start loading data '%s' ...", handwriting_datasets_file)
    loaded = pickle.load(open(handwriting_datasets_file))
    raw_datasets = loaded['handwriting_datasets']
    logging.info("%i datasets loaded.", len(raw_datasets))
    logging.info("Start analyzing...")

    if analyze_features:
        featurelist = [(features.AspectRatio(), "aspect_ratio.csv"),
                       (features.ReCurvature(1), "re_curvature.csv"),
                       (features.Height(), "height.csv"),
                       (features.Width(), "width.csv"),
                       (features.Time(), "time.csv"),
                       (features.Ink(), "ink.csv"),
                       (features.StrokeCount(), "stroke-count.csv")]
        for feat, filename in featurelist:
            logging.info("create %s...", filename)
            analyze_feature(raw_datasets, feat, filename)

    # Analyze everything specified in configuration
    cfg = utils.get_project_configuration()
    if 'data_analyzation_queue' in cfg:
        metrics = dam.get_metrics(cfg['data_analyzation_queue'])
        for metric in metrics:
            logging.info("Start metric %s...", str(metric))
            metric(raw_datasets)
    else:
        logging.info("No 'data_analyzation_queue' in ~/.hwrtrc")


def get_parser():
    """Return the parser object for this script."""
    project_root = utils.get_project_root()

    # Get latest (raw) dataset
    dataset_folder = os.path.join(project_root, "raw-datasets")
    latest_dataset = utils.get_latest_in_folder(dataset_folder, "raw.pickle")

    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--handwriting_datasets",
                        dest="handwriting_datasets",
                        help="where are the pickled handwriting_datasets?",
                        metavar="FILE",
                        type=lambda x: utils.is_valid_file(parser, x),
                        default=latest_dataset)
    parser.add_argument("-f", "--features",
                        dest="analyze_features",
                        help="analyze features",
                        action="store_true",
                        default=False)
    return parser


if __name__ == '__main__':
    args = get_parser().parse_args()
    main(args.handwriting_datasets, args.analyze_features)
