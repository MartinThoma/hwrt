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
# mine
import hwrt
from hwrt.HandwrittenData import HandwrittenData
import hwrt.utils as utils
import hwrt.preprocessing as preprocessing
import hwrt.features as features
import hwrt.data_multiplication as data_multiplication


def fetch_data(raw_data_id):
    """Get the data from raw_data_id from the server."""
    # Import configuration file
    cfg = utils.get_database_configuration()

    # Establish database connection
    connection = MySQLdb.connect(host=cfg[args.mysql]['host'],
                                 user=cfg[args.mysql]['user'],
                                 passwd=cfg[args.mysql]['passwd'],
                                 db=cfg[args.mysql]['db'],
                                 cursorclass=MySQLdb.cursors.DictCursor)
    cursor = connection.cursor()

    # Download dataset
    sql = ("SELECT `id`, `data` "
           "FROM `wm_raw_draw_data` WHERE `id`=%i") % args.id
    cursor.execute(sql)
    data = cursor.fetchone()
    return data


def display_data(raw_data_string, raw_data_id, model_folder):
    print("#### Raw Data (ID: %i)" % raw_data_id)
    print("```")
    print(raw_data_string)
    print("```")

    PROJECT_ROOT = utils.get_project_root()

    # Get model description
    model_description_file = os.path.join(model_folder, "info.yml")
    if not os.path.isfile(model_description_file):
        logging.error("You are probably not in the folder of a model, because "
                      "%s is not a file. (-m argument)",
                      model_description_file)
        sys.exit(-1)
    with open(model_description_file, 'r') as ymlfile:
        model_description = yaml.load(ymlfile)

    # Get the feature description
    feature_description_file = os.path.join(PROJECT_ROOT,
                                            model_description['data-source'],
                                            "info.yml")
    if not os.path.isfile(feature_description_file):
        logging.error("You are probably not in the folder of a model, because "
                      "%s is not a file.", feature_description_file)
        sys.exit(-1)
    with open(feature_description_file, 'r') as ymlfile:
        feature_description = yaml.load(ymlfile)

    # Get the preprocessing description
    preprocessing_description_file = os.path.join(
        PROJECT_ROOT,
        feature_description['data-source'],
        "info.yml")
    if not os.path.isfile(preprocessing_description_file):
        logging.error("You are probably not in the folder of a model, because "
                      "%s is not a file.", preprocessing_description_file)
        sys.exit(-1)
    with open(preprocessing_description_file, 'r') as ymlfile:
        preprocessing_description = yaml.load(ymlfile)

    # Print preprocessing queue
    print("#### Preprocessing")
    print("```")
    tmp = preprocessing_description['queue']
    preprocessing_queue = preprocessing.get_preprocessing_queue(tmp)
    for algorithm in preprocessing_queue:
        print("* " + str(algorithm))
    print("```")

    feature_list = features.get_features(feature_description['features'])
    INPUT_FEATURES = sum(map(lambda n: n.get_dimension(), feature_list))
    print("#### Features (%i)" % INPUT_FEATURES)
    print("```")
    for algorithm in feature_list:
        print("* %s" % str(algorithm))
    print("```")

    # Get Handwriting
    a = HandwrittenData(raw_data_string, raw_data_id=raw_data_id)

    # Get the preprocessing queue
    tmp = preprocessing_description['queue']
    preprocessing_queue = preprocessing.get_preprocessing_queue(tmp)
    a.preprocessing(preprocessing_queue)

    tmp = feature_description['features']
    feature_list = features.get_features(tmp)
    x = a.feature_extraction(feature_list)
    t = [round(el, 3) for el in x]
    print("Features:")
    print(t)

    # Get the list of data multiplication algorithms
    mult_queue = data_multiplication.get_data_multiplication_queue(
        feature_description['data-multiplication'])

    # Multiply traing_set
    training_set = [a]
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
    PROJECT_ROOT = utils.get_project_root()

    # Get latest model description file
    models_folder = os.path.join(PROJECT_ROOT, "models")
    latest_model = utils.get_latest_in_folder(models_folder, ".yml")

    # Parse command line arguments
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
                        default=latest_model)
    return parser

if __name__ == '__main__':
    args = get_parser().parse_args()

    # do something
    data = fetch_data(args.id)
    if data is None:
        print("RAW_DATA_ID %i does not exist." % args.id)
    else:
        print("hwrt version: %s" % hwrt.__version__)
        display_data(data['data'], data['id'], args.model)
