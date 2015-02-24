#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Display a recorded handwritten symbol as well as the preprocessing methods
and the data multiplication steps that get applied.
"""

import logging
import sys
import os
import yaml
try:  # Python 2
    import cPickle as pickle
except ImportError:  # Python 3
    import pickle

# hwrt modules
import hwrt
from hwrt import HandwrittenData
sys.modules['HandwrittenData'] = HandwrittenData
import hwrt.utils as utils
import hwrt.preprocessing as preprocessing
import hwrt.features as features
import hwrt.data_multiplication as data_multiplication
import hwrt.create_pfiles as create_pfiles


def _fetch_data_from_server(raw_data_id, mysql_cfg):
    """Get the data from raw_data_id from the server.
    :returns: The ``data`` if fetching worked, ``None`` if it failed."""
    import pymysql
    import pymysql.cursors

    # Import configuration file
    cfg = utils.get_database_configuration()
    if cfg is None:
        return None

    # Establish database connection
    connection = pymysql.connect(host=cfg[mysql_cfg]['host'],
                                 user=cfg[mysql_cfg]['user'],
                                 passwd=cfg[mysql_cfg]['passwd'],
                                 db=cfg[mysql_cfg]['db'],
                                 cursorclass=pymysql.cursors.DictCursor)
    logging.info("Connection: %s", str(connection))
    cursor = connection.cursor()

    # Download dataset
    sql = ("SELECT `id`, `data` "
           "FROM `wm_raw_draw_data` WHERE `id`=%i") % raw_data_id
    cursor.execute(sql)
    return cursor.fetchone()


def _get_data_from_rawfile(path_to_data, raw_data_id):
    """Get a HandwrittenData object that has ``raw_data_id`` from a pickle file
       ``path_to_data``.
       :returns: The HandwrittenData object if ``raw_data_id`` is in
                 path_to_data, otherwise ``None``."""
    loaded = pickle.load(open(path_to_data, "rb"))
    raw_datasets = loaded['handwriting_datasets']
    for raw_dataset in raw_datasets:
        if raw_dataset['handwriting'].raw_data_id == raw_data_id:
            return raw_dataset['handwriting']
    return None


def _list_ids(path_to_data):
    """List raw data IDs grouped by symbol ID from a pickle file
       ``path_to_data``."""
    loaded = pickle.load(open(path_to_data, "rb"))
    raw_datasets = loaded['handwriting_datasets']
    raw_ids = {}
    for raw_dataset in raw_datasets:
        raw_data_id = raw_dataset['handwriting'].raw_data_id
        if raw_dataset['formula_id'] not in raw_ids:
            raw_ids[raw_dataset['formula_id']] = [raw_data_id]
        else:
            raw_ids[raw_dataset['formula_id']].append(raw_data_id)
    for symbol_id in sorted(raw_ids):
        print("%i: %s" % (symbol_id, sorted(raw_ids[symbol_id])))


def _get_description(prev_description):
    """Get the parsed description file (a dictionary) from another
       parsed description file."""
    current_desc_file = os.path.join(utils.get_project_root(),
                                     prev_description['data-source'],
                                     "info.yml")
    if not os.path.isfile(current_desc_file):
        logging.error("You are probably not in the folder of a model, because "
                      "%s is not a file.", current_desc_file)
        sys.exit(-1)
    with open(current_desc_file, 'r') as ymlfile:
        current_description = yaml.load(ymlfile)
    return current_description


def _get_system(model_folder):
    """Return the preprocessing description, the feature description and the
       model description."""

    # Get model description
    model_description_file = os.path.join(model_folder, "info.yml")
    if not os.path.isfile(model_description_file):
        logging.error("You are probably not in the folder of a model, because "
                      "%s is not a file. (-m argument)",
                      model_description_file)
        sys.exit(-1)
    with open(model_description_file, 'r') as ymlfile:
        model_desc = yaml.load(ymlfile)

    # Get the feature and the preprocessing description
    feature_desc = _get_description(model_desc)
    preprocessing_desc = _get_description(feature_desc)

    return (preprocessing_desc, feature_desc, model_desc)


def display_data(raw_data_string, raw_data_id, model_folder, show_raw):
    """Print ``raw_data_id`` with the content ``raw_data_string`` after
       applying the preprocessing of ``model_folder`` to it."""
    print("## Raw Data (ID: %i)" % raw_data_id)
    print("```")
    print(raw_data_string)
    print("```")

    preprocessing_desc, feature_desc, _ = _get_system(model_folder)

    # Print model
    print("## Model")
    print("%s\n" % model_folder)

    # Get the preprocessing queue
    tmp = preprocessing_desc['queue']
    preprocessing_queue = preprocessing.get_preprocessing_queue(tmp)

    # Get feature values as list of floats, rounded to 3 decimal places
    tmp = feature_desc['features']
    feature_list = features.get_features(tmp)

    # Print preprocessing queue
    preprocessing.print_preprocessing_list(preprocessing_queue)
    features.print_featurelist(feature_list)

    # Get Handwriting
    recording = HandwrittenData.HandwrittenData(raw_data_string,
                                                raw_data_id=raw_data_id)
    if show_raw:
        recording.show()

    recording.preprocessing(preprocessing_queue)

    feature_values = recording.feature_extraction(feature_list)
    feature_values = [round(el, 3) for el in feature_values]
    print("Features:")
    print(feature_values)

    # Get the list of data multiplication algorithms
    mult_queue = data_multiplication.get_data_multiplication_queue(
        feature_desc['data-multiplication'])

    # Multiply traing_set
    training_set = [{'id': 42,
                     'formula_id': 42,
                     'formula_in_latex': 'None',
                     'handwriting': recording}]
    training_set = create_pfiles.training_set_multiplication(training_set,
                                                             mult_queue)

    # Display it
    logging.info("Show %i recordings...", len(training_set))
    for recording in training_set:
        recording['handwriting'].show()


def get_parser():
    """Return the parser object for this script."""
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--id", dest="id", default=292293,
                        type=int,
                        help="which RAW_DATA_ID do you want?")
    parser.add_argument("--mysql", dest="mysql", default='mysql_online',
                        help="which mysql configuration should be used?")
    parser.add_argument("-m", "--model",
                        dest="model",
                        help="where is the model folder (with a info.yml)?",
                        metavar="FOLDER",
                        type=lambda x: utils.is_valid_folder(parser, x),
                        default=utils.default_model())
    parser.add_argument("-l", "--list",
                        dest="list",
                        help="list all raw data IDs / symbol IDs",
                        action='store_true',
                        default=False)
    parser.add_argument("-s", "--server",
                        dest="server",
                        help="contact the MySQL server",
                        action='store_true',
                        default=False)
    parser.add_argument("-r", "--raw",
                        dest="show_raw",
                        help="show the raw recording (without preprocessing)",
                        action='store_true',
                        default=False)
    return parser


def main(list_ids, model, contact_server, raw_data_id, show_raw,
         mysql_cfg='mysql_online'):
    """Main function of view.py."""
    if list_ids:
        preprocessing_desc, _, _ = _get_system(model)
        raw_datapath = os.path.join(utils.get_project_root(),
                                    preprocessing_desc['data-source'])
        _list_ids(raw_datapath)
    else:
        if contact_server:
            data = _fetch_data_from_server(raw_data_id, mysql_cfg)
            print("hwrt version: %s" % hwrt.__version__)
            if data is not None:
                display_data(data['data'], data['id'], model, show_raw)
        else:
            logging.info("RAW_DATA_ID %i does not exist or "
                         "database connection did not work.", raw_data_id)
            # The data was not on the server / the connection to the server did
            # not work. So try it again with the model data
            preprocessing_desc, _, _ = _get_system(model)
            raw_datapath = os.path.join(utils.get_project_root(),
                                        preprocessing_desc['data-source'])
            handwriting = _get_data_from_rawfile(raw_datapath, raw_data_id)
            if handwriting is None:
                logging.info("Recording with ID %i was not found in %s",
                             raw_data_id,
                             raw_datapath)
            else:
                print("hwrt version: %s" % hwrt.__version__)
                display_data(handwriting.raw_data_json,
                             handwriting.formula_id,
                             model,
                             show_raw)

if __name__ == '__main__':
    args = get_parser().parse_args()
    main(args.list, args.model, args.server, args.id, args.show_raw,
         args.mysql)
