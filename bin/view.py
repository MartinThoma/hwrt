#!/usr/bin/env python
"""
Display a raw_data_id.
"""

import sys
import os
import logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)
import yaml
import MySQLdb
import MySQLdb.cursors
import cPickle as pickle
# mine
import hwrt
from hwrt.HandwrittenData import HandwrittenData
import hwrt.utils as utils
import hwrt.preprocessing as preprocessing
import hwrt.features as features
import hwrt.data_multiplication as data_multiplication


def _fetch_data_from_server(raw_data_id):
    """Get the data from raw_data_id from the server.
    :returns: The ``data`` if fetching worked, ``None`` if it failed."""
    # Import configuration file
    cfg = utils.get_database_configuration()
    if cfg is None:
        return None

    # Establish database connection
    connection = MySQLdb.connect(host=cfg[args.mysql]['host'],
                                 user=cfg[args.mysql]['user'],
                                 passwd=cfg[args.mysql]['passwd'],
                                 db=cfg[args.mysql]['db'],
                                 cursorclass=MySQLdb.cursors.DictCursor)
    cursor = connection.cursor()

    # Download dataset
    sql = ("SELECT `id`, `data` "
           "FROM `wm_raw_draw_data` WHERE `id`=%i") % raw_data_id
    cursor.execute(sql)
    return cursor.fetchone()


def _get_data_from_rawfile(path_to_data, raw_data_id):
    """Get a HandwrittenData object that has ``raw_data_id`` from a pickle file
       ``path_to_data``."""
    loaded = pickle.load(open(path_to_data))
    raw_datasets = loaded['handwriting_datasets']
    for raw_dataset in raw_datasets:
        if raw_dataset['handwriting'].raw_data_id == raw_data_id:
            return raw_dataset['handwriting']
    return None


def _list_ids(path_to_data):
    """List raw data IDs grouped by symbol ID from a pickle file
       ``path_to_data``."""
    loaded = pickle.load(open(path_to_data))
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


def _get_system(model_folder):
    """Return the preprocessing description, the feature description and the
       model description."""
    project_root = utils.get_project_root()

    # Get model description
    model_description_file = os.path.join(model_folder, "info.yml")
    if not os.path.isfile(model_description_file):
        logging.error("You are probably not in the folder of a model, because "
                      "%s is not a file. (-m argument)",
                      model_description_file)
        sys.exit(-1)
    with open(model_description_file, 'r') as ymlfile:
        model_desc = yaml.load(ymlfile)

    # Get the feature description
    feature_description_file = os.path.join(project_root,
                                            model_desc['data-source'],
                                            "info.yml")
    if not os.path.isfile(feature_description_file):
        logging.error("You are probably not in the folder of a model, because "
                      "%s is not a file.", feature_description_file)
        sys.exit(-1)
    with open(feature_description_file, 'r') as ymlfile:
        feature_desc = yaml.load(ymlfile)

    # Get the preprocessing description
    preprocessing_description_file = os.path.join(
        project_root,
        feature_desc['data-source'],
        "info.yml")
    if not os.path.isfile(preprocessing_description_file):
        logging.error("You are probably not in the folder of a model, because "
                      "%s is not a file.", preprocessing_description_file)
        sys.exit(-1)
    with open(preprocessing_description_file, 'r') as ymlfile:
        preprocessing_desc = yaml.load(ymlfile)

    return (preprocessing_desc, feature_desc, model_desc)


def display_data(raw_data_string, raw_data_id, model_folder):
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

    # Print preprocessing queue
    print("## Preprocessing")
    print("```")
    tmp = preprocessing_desc['queue']
    preprocessing_queue = preprocessing.get_preprocessing_queue(tmp)
    for algorithm in preprocessing_queue:
        print("* " + str(algorithm))
    print("```")

    feature_list = features.get_features(feature_desc['features'])
    input_features = sum(map(lambda n: n.get_dimension(), feature_list))
    print("## Features (%i)" % input_features)
    print("```")
    for algorithm in feature_list:
        print("* %s" % str(algorithm))
    print("```")

    # Get Handwriting
    recording = HandwrittenData(raw_data_string, raw_data_id=raw_data_id)

    # Get the preprocessing queue
    tmp = preprocessing_desc['queue']
    preprocessing_queue = preprocessing.get_preprocessing_queue(tmp)
    recording.preprocessing(preprocessing_queue)

    tmp = feature_desc['features']
    feature_list = features.get_features(tmp)
    feature_values = recording.feature_extraction(feature_list)
    feature_values = [round(el, 3) for el in feature_values]
    print("Features:")
    print(feature_values)

    # Get the list of data multiplication algorithms
    mult_queue = data_multiplication.get_data_multiplication_queue(
        feature_desc['data-multiplication'])

    # Multiply traing_set
    training_set = [recording]
    for algorithm in mult_queue:
        new_trning_set = []
        for recording in training_set:
            samples = algorithm(recording)
            for sample in samples:
                new_trning_set.append(sample)
        training_set = new_trning_set

    # Display it
    for recording in training_set:
        recording.show()


def get_parser():
    """Return the parser object for this script."""
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--id", dest="id", default=279062,
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
    return parser

if __name__ == '__main__':
    args = get_parser().parse_args()
    if args.list:
        preprocessing_desc, _, _ = _get_system(args.model)
        raw_datapath = os.path.join(utils.get_project_root(),
                                    preprocessing_desc['data-source'])
        _list_ids(raw_datapath)
    else:
        data = _fetch_data_from_server(args.id)
        if data is None:
            logging.info("RAW_DATA_ID %i does not exist or "
                         "database connection did not work.", args.id)
            # The data was not on the server / the connection to the server did
            # not work. So try it again with the model data
            preprocessing_desc, _, _ = _get_system(args.model)
            raw_datapath = os.path.join(utils.get_project_root(),
                                        preprocessing_desc['data-source'])
            handwriting = _get_data_from_rawfile(raw_datapath, args.id)
            if handwriting is None:
                logging.info("Recording with ID %i was not found in %s",
                             args.id,
                             raw_datapath)
            else:
                print("hwrt version: %s" % hwrt.__version__)
                display_data(handwriting.raw_data_json,
                             handwriting.formula_id,
                             args.model)
        else:
            print("hwrt version: %s" % hwrt.__version__)
            display_data(data['data'], data['id'], args.model)
