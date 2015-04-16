#!/usr/bin/env python

"""Script to import data into write-math.com"""

import logging
import sys

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)

import pymysql
import pymysql.cursors

# hwrt modules
from hwrt import utils
from hwrt.datasets import mfrdb


def insert_recording(hw, info):
    cfg = utils.get_database_configuration()
    mysql = cfg['mysql_online']
    connection = pymysql.connect(host=mysql['host'],
                                 user=mysql['user'],
                                 passwd=mysql['passwd'],
                                 db=mysql['db'],
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    try:
        cursor = connection.cursor()
        sql = ("INSERT INTO `wm_raw_draw_data` ("
               "`user_id`, "
               "`data`, "
               "`md5data`, "
               "`creation_date`, "
               "`device_type`, "
               "`accepted_formula_id`, "
               "`secret`, "
               "`ip`, "
               "`description` "
               ") VALUES (%s, %s, MD5(data), "
               "%s, %s, %s, %s, %s, %s);")
        cursor.execute(sql, (info['userid'],
                             hw.raw_data_json,
                             info['creation_date'],
                             info['device_type'],
                             info['accepted_formula_id'],
                             info['secret'],
                             info['ip'],
                             info['rec_desc']))
        connection.commit()
    except pymysql.err.IntegrityError as e:
        print("Error: {} (can probably be ignored)".format(e))


def main(directory):
    recordings = mfrdb.get_recordings(directory)
    logging.info("Got recordings for %i symbols.", len(recordings))
    recordings = sorted(recordings, key=lambda n: len(n[1]))
    for symbol, symbol_recs in recordings:
        logging.info("{0:>10}: {1} recordings".format(symbol,
                                                      len(symbol_recs)))
        for hw, info in symbol_recs:
            pass
            #insert_recording(hw, info)
    logging.info("Done importing dataset")


if __name__ == '__main__':
    main("/home/moose/Downloads/MfrDB_Symbols_v1.0")
