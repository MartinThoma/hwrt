#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Download raw data from online server and store it as csv files.
"""

import logging
import sys
import os
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.INFO,
                    stream=sys.stdout)
import pymysql
import pymysql.cursors
import csv
import time
import tarfile

# hwrt modules
from hwrt.HandwrittenData import HandwrittenData
import hwrt.utils as utils


def main(destination):
    """Main part of the backup script."""
    cfg = utils.get_database_configuration()
    mysql = cfg['mysql_online']
    connection = pymysql.connect(host=mysql['host'],
                                 user=mysql['user'],
                                 passwd=mysql['passwd'],
                                 db=mysql['db'],
                                 cursorclass=pymysql.cursors.DictCursor)
    cursor = connection.cursor()

    # Get all formulas that should get examined
    sql = ("SELECT `id`, `formula_in_latex` FROM `wm_formula` "
           # only use the important symbol subset
           "WHERE `is_important` = 1 "
           "AND id != 1 "  # exclude trash class
           #"AND id < 40 "  # TODO: Only for testing
           "ORDER BY `id` ASC")
    cursor.execute(sql)
    formulas = cursor.fetchall()

    handwriting_datasets = []
    formula_id2latex = {}

    formulas_csv = {}

    # Go through each formula and download every raw_data instance
    for formula in formulas:
        formula_id2latex[formula['id']] = formula['formula_in_latex']
        sql = ("SELECT `id`, `data`, `is_in_testset`, `wild_point_count`, "
               "`missing_line`, `user_id`, `user_agent` "
               "FROM `wm_raw_draw_data` "
               "WHERE `accepted_formula_id` = %s" % str(formula['id']))
        cursor.execute(sql)
        raw_datasets = cursor.fetchall()
        logging.info("%s (%i)", formula['formula_in_latex'], len(raw_datasets))
        for raw_data in raw_datasets:
            try:
                handwriting = HandwrittenData(raw_data['data'],
                                              formula['id'],
                                              raw_data['id'],
                                              formula['formula_in_latex'],
                                              raw_data['wild_point_count'],
                                              raw_data['missing_line'],
                                              raw_data['user_id'])
                handwriting_datasets.append({'handwriting': handwriting,
                                             'is_in_testset':
                                             raw_data['is_in_testset'],
                                             'user_agent': raw_data['user_agent']})
                if formula['id'] not in formulas_csv:
                    formulas_csv[formula['id']] = {'training_samples': 0,
                                                   'test_samples': 0,
                                                   'latex': formula['formula_in_latex']}
                if raw_data['is_in_testset']:
                    formulas_csv[formula['id']]['test_samples'] += 1
                else:
                    formulas_csv[formula['id']]['training_samples'] += 1

            except Exception as e:
                logging.info("Raw data id: %s", raw_data['id'])
                logging.info(e)

    # Write data
    with open('train-data.csv', 'wb') as csvfile:
        spamwriter = csv.writer(csvfile,
                                delimiter=';',
                                quotechar="'",
                                quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(['symbol_id', 'user_id', 'data', 'user_agent'])
        for data in handwriting_datasets:
            if not data['is_in_testset']:
                spamwriter.writerow([data['handwriting'].formula_id,
                                     data['handwriting'].user_id,
                                     data['handwriting'].raw_data_json,
                                     data['user_agent']])

    with open('test-data.csv', 'wb') as csvfile:
        spamwriter = csv.writer(csvfile,
                                delimiter=';',
                                quotechar="'",
                                quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(['symbol_id', 'user_id', 'data', 'user_agent'])
        for data in handwriting_datasets:
            if data['is_in_testset']:
                spamwriter.writerow([data['handwriting'].formula_id,
                                     data['handwriting'].user_id,
                                     data['handwriting'].raw_data_json,
                                     data['user_agent']])

    with open('symbols.csv', 'wb') as csvfile:
        spamwriter = csv.writer(csvfile,
                                delimiter=';',
                                quotechar="'",
                                quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(['symbol_id',
                             'latex',
                             'training_samples',
                             'test_samples'])
        for symbol_id, data in sorted(formulas_csv.items()):
            spamwriter.writerow([symbol_id,
                                 data['latex'],
                                 data['training_samples'],
                                 data['test_samples']])

    time_prefix = time.strftime("%Y-%m-%d-%H-%M")
    archive_filename = "%s-data.tar" % time_prefix
    filenames = ['symbols.csv', 'test-data.csv', 'train-data.csv']
    # Create tar file
    with tarfile.open(archive_filename, "w:bz2") as tar:
        for name in filenames:
            tar.add(name)

    # Remove temporary files which are now in tar file
    for filename in filenames:
        os.remove(filename)


def get_parser():
    """Return the parser object for this script."""
    project_root = utils.get_project_root()
    archive_path = os.path.join(project_root, "raw-datasets")
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--destination", dest="destination",
                        default=archive_path,
                        help="where do write the handwriting_dataset.pickle",
                        type=lambda x: utils.is_valid_file(parser, x),
                        metavar="FOLDER")
    return parser


if __name__ == '__main__':
    args = get_parser().parse_args()
    main(args.destination)
