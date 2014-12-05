#!/usr/bin/env python

"""
Add `is_in_testset` to raw_datasets in MySQL database, so that at least 10%
of the data online has the flag `is_in_testset`.
"""

import pymysql
import pymysql.cursors
import random
import math

# hwrt modules
from hwrt.HandwrittenData import HandwrittenData
import hwrt.utils as utils


def main(mysql):
    """Add testset flag to recordings in MySQL database."""
    connection = pymysql.connect(host=mysql['host'],
                                 user=mysql['user'],
                                 passwd=mysql['passwd'],
                                 db=mysql['db'],
                                 cursorclass=pymysql.cursors.DictCursor)
    cursor = connection.cursor()

    # Download all datasets
    sql = ("SELECT `id`, `formula_in_latex` FROM `wm_formula` "
           "WHERE `is_important` = 1 ORDER BY `id` ASC")
    cursor.execute(sql)
    datasets = cursor.fetchall()

    for i, data in enumerate(datasets):
        fid, formula_in_latex = data['id'], data['formula_in_latex']
        print("%i: Create testset for %s (id: %i)..." % (i,
                                                         formula_in_latex,
                                                         fid))
        sql = ("SELECT `id`, `is_in_testset` FROM `wm_raw_draw_data` "
               "WHERE `accepted_formula_id` = %i" % fid)
        cursor.execute(sql)
        raw_datasets = cursor.fetchall()
        is_in_testset = 0
        raw_candidate_ids = []
        for j, raw_data in enumerate(raw_datasets):
            if raw_data['is_in_testset'] == 1:
                is_in_testset += 1
            else:
                raw_candidate_ids.append(raw_data['id'])
        testset_ratio = 0.1
        testset_total = int(math.ceil(len(raw_datasets)*testset_ratio))
        remaining = testset_total - is_in_testset

        if remaining > 0:
            print("%i in testset. Add remaining %i datasets to testset..." %
                  (is_in_testset, remaining))
            add_new = random.sample(raw_candidate_ids, remaining)
            if len(add_new) < 20:
                for el in add_new:
                    print("http://write-math.com/view/?raw_data_id=%i" % el)
            for rid in add_new:
                sql = ("UPDATE `wm_raw_draw_data` SET `is_in_testset`=1 "
                       "WHERE `id` = %i LIMIT 1") % rid
                cursor.execute(sql)
            connection.commit()


def get_parser():
    """Return the parser object for this script."""
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    return parser


if __name__ == '__main__':
    args = get_parser().parse_args()
    cfg = utils.get_database_configuration()
    if 'mysql_online' in cfg:
        main(cfg['mysql_online'])
    if 'mysql_local' in cfg:
        main(cfg['mysql_local'])
