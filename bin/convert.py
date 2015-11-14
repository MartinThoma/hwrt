#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Convert an old-style DETL model to a nntoolkit model."""

import numpy as np

from base64 import b64encode, b64decode
from StringIO import StringIO
import yaml
import h5py
import tarfile
import os
import csv
import logging

# hwrt modules
import hwrt.utils as utils


def _array2cstr(arr):
    """ Serializes a numpy array to a compressed base64 string """
    out = StringIO()
    np.save(out, arr)
    return b64encode(out.getvalue())


def _str2array(d):
    """ Reconstructs a numpy array from a plain-text string """
    if type(d) == list:
        return np.asarray([_str2array(s) for s in d])
    ins = StringIO(d)
    return np.loadtxt(ins)


def _cstr2array(d):
    """ Reconstructs a numpy array from a compressed base64 string """
    ins = StringIO(b64decode(d))
    return np.load(ins)


def _as_ndarray(dct):
    if '__numpy.ndarray__' in dct:
        return _str2array(dct['__numpy.ndarray__'])
    elif '__numpy.cndarray__' in dct:
        return _cstr2array(dct['__numpy.cndarray__'])
    return dct


def create_output_semantics(model_folder, outputs):
    """
    Create a 'output_semantics.csv' file which contains information what the
    output of the single output neurons mean.

    Parameters
    ----------
    model_folder : str
        folder where the model description file is
    outputs : int
        number of output neurons
    """
    with open('output_semantics.csv', 'wb') as csvfile:
        model_description_file = os.path.join(model_folder, "info.yml")
        with open(model_description_file, 'r') as ymlfile:
            model_description = yaml.load(ymlfile)

        logging.info("Start fetching translation dict...")
        translation_dict = utils.get_index2data(model_description)
        spamwriter = csv.writer(csvfile, delimiter=';',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for output_index in range(outputs):
            if output_index in translation_dict:
                # Add more information:
                # 1. ID in my system
                # 2. latex
                # 3. unicode code point
                # 4. font
                # 5. font style
                spamwriter.writerow(translation_dict[output_index])
            else:
                print("No data for %i." % output_index)
                spamwriter.writerow(["output %i" % output_index])


def main(model_folder):
    a = yaml.load(open(utils.get_latest_in_folder(model_folder, ".json")))

    layers = []
    filenames = ["model.yml", "input_semantics.csv", "output_semantics.csv",
                 "preprocessing.yml", "features.yml"]

    # Create input_semantics.csv
    inputs = a['layers'][0]['_props']['n_visible']
    with open('input_semantics.csv', 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=';',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in range(inputs):
            spamwriter.writerow(["inputs %i" % row])

    # Create output_semantics.csv
    outputs = a['layers'][-1]['_props']['n_hidden']
    create_output_semantics(model_folder, outputs)

    # Write layers
    for layer in range(len(a['layers'])):
        W = _as_ndarray(a['layers'][layer]['params']['W'])
        Wfile = h5py.File('W%i.hdf5' % layer, 'w')
        Wfile.create_dataset(Wfile.id.name, data=W)
        Wfile.close()

        b = _as_ndarray(a['layers'][layer]['params']['b'])
        bfile = h5py.File('b%i.hdf5' % layer, 'w')
        bfile.create_dataset(bfile.id.name, data=b)
        bfile.close()

        activation = a['layers'][layer]['_props']['activation']
        activation = activation.replace('sigmoid', 'Sigmoid')
        activation = activation.replace('softmax', 'Softmax')
        layers.append({'W': {'size': list(W.shape),
                             'filename': 'W%i.hdf5' % layer},
                       'b': {'size': list(b.shape),
                             'filename': 'b%i.hdf5' % layer},
                       'activation': activation})
        filenames.append('W%i.hdf5' % layer)
        filenames.append('b%i.hdf5' % layer)

    model = {'type': 'mlp', 'layers': layers}

    with open("model.yml", 'w') as f:
        yaml.dump(model, f, default_flow_style=False)

    logging.info("Get preprocessing.yml")
    # Get model folder
    model_description_file = os.path.join(model_folder, "info.yml")
    with open(model_description_file, 'r') as ymlfile:
        model_description = yaml.load(ymlfile)

    # Get feature folder
    feature_description_file = os.path.join(utils.get_project_root(),
                                            model_description["data-source"],
                                            "info.yml")
    with open(feature_description_file, 'r') as ymlfile:
        feature_description = yaml.load(ymlfile)

    with open("features.yml", 'w') as f:
        yaml.dump(feature_description, f, default_flow_style=False)

    # Get preprocessing folder
    preprocessing_description_file = os.path.join(utils.get_project_root(),
                                                  feature_description["data-source"],
                                                  "info.yml")
    with open(preprocessing_description_file, 'r') as ymlfile:
        preprocessing_description = yaml.load(ymlfile)

    with open("preprocessing.yml", 'w') as f:
        yaml.dump(preprocessing_description, f, default_flow_style=False)

    with tarfile.open("model.tar", "w:") as tar:
        for name in filenames:
            tar.add(name)

    # Remove temporary files which are now in tar file
    for filename in filenames:
        os.remove(filename)


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
