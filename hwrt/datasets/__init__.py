"""Utility functions to work with other datasets."""

import logging
import sys

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)

import pymysql
import pymysql.cursors

# hwrt modules
from hwrt import utils

__formula_to_dbid_cache = None
username2id = {}


def formula_to_dbid(formula_str, backslash_fix=False):
    """Convert a LaTeX formula to the database index.

    Parameters
    ----------
    formula_str : string
        The formula as LaTeX code.
    backslash_fix : boolean
        If this is set to true, then it will be checked if the same formula
        exists with a preceeding backslash.

    Returns
    -------
    int :
        The database index.
    """
    global __formula_to_dbid_cache
    if __formula_to_dbid_cache is None:
        cfg = utils.get_database_configuration()
        mysql = cfg['mysql_dev']
        connection = pymysql.connect(host=mysql['host'],
                                     user=mysql['user'],
                                     passwd=mysql['passwd'],
                                     db=mysql['db'],
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()

        # Get all formulas that should get examined
        sql = ("SELECT `id`, `formula_in_latex` FROM `wm_formula` ")
        cursor.execute(sql)
        formulas = cursor.fetchall()
        __formula_to_dbid_cache = {}
        for fm in formulas:
            __formula_to_dbid_cache[fm['formula_in_latex']] = fm['id']
    if formula_str in __formula_to_dbid_cache:
        return __formula_to_dbid_cache[formula_str]
    elif backslash_fix and ('\\%s' % formula_str) in __formula_to_dbid_cache:
        return __formula_to_dbid_cache['\\%s' % formula_str]
    else:
        cfg = utils.get_database_configuration()
        mysql = cfg['mysql_dev']
        connection = pymysql.connect(host=mysql['host'],
                                     user=mysql['user'],
                                     passwd=mysql['passwd'],
                                     db=mysql['db'],
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()
        sql = ("INSERT INTO `wm_formula` (`user_id`, `formula_name`, "
               "`formula_in_latex`, "
               "`mode`, `package`, "
               "`is_important`) VALUES ("
               "'10', %s, %s, 'bothmodes', NULL, '0');")
        if len(formula_str) < 20:
            logging.info("Insert formula %s.", formula_str)
        cursor.execute(sql, (formula_str, formula_str))
        connection.commit()
        __formula_to_dbid_cache[formula_str] = connection.insert_id()
        return __formula_to_dbid_cache[formula_str]


def getuserid(username, copyright_str):
    """Get the ID of the user with `username` from write-math.com. If he
    doesn't exist by now, create it. Add `copyright_str` as a description.

    Parameters
    ----------
    username : string
        Name of a user.
    copyright_str : string
        Description text of a user in Markdown format.

    Returns
    -------
    int :
        ID on write-math.com of the user.
    """
    global username2id
    if username not in username2id:
        cfg = utils.get_database_configuration()
        mysql = cfg['mysql_dev']
        connection = pymysql.connect(host=mysql['host'],
                                     user=mysql['user'],
                                     passwd=mysql['passwd'],
                                     db=mysql['db'],
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()

        sql = ("INSERT IGNORE INTO  `wm_users` ("
               "`display_name` , "
               "`password` ,"
               "`account_type` ,"
               "`confirmation_code` ,"
               "`status` ,"
               "`description`"
               ") "
               "VALUES ("
               "%s, '',  'Regular User',  '',  'activated', %s"
               ");")
        cursor.execute(sql, (username, copyright_str))
        connection.commit()

        # Get the id
        try:
            sql = ("SELECT  `id` FROM  `wm_users` "
                   "WHERE  `display_name` =  %s LIMIT 1")
            cursor.execute(sql, username)
            uid = cursor.fetchone()['id']
        except Exception as inst:
            logging.debug("username not found: %s", username)
            print(inst)
        # logging.info("%s: %s", username, uid)
        username2id[username] = uid
    return username2id[username]


def insert_recording(hw):
    """Insert recording `hw` into database."""
    cfg = utils.get_database_configuration()
    mysql = cfg['mysql_dev']
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
               "`segmentation`, "
               "`internal_id`, "
               "`description` "
               ") VALUES (%s, %s, MD5(data), "
               "%s, %s, %s, %s, %s, %s, %s, %s);")
        data = (hw.user_id,
                hw.raw_data_json,
                getattr(hw, 'creation_date', None),
                getattr(hw, 'device_type', ''),
                getattr(hw, 'formula_id', None),
                getattr(hw, 'secret', ''),
                getattr(hw, 'ip', None),
                str(getattr(hw, 'segmentation', '')),
                getattr(hw, 'internal_id', ''),
                getattr(hw, 'description', ''))
        cursor.execute(sql, data)
        connection.commit()
        for symbol_id, strokes in zip(hw.symbol_stream, hw.segmentation):
            insert_symbol_mapping(cursor.lastrowid, symbol_id, hw.user_id, strokes)
        logging.info("Insert raw data.")
    except pymysql.err.IntegrityError as e:
        print("Error: {} (can probably be ignored)".format(e))


def insert_symbol_mapping(raw_data_id, symbol_id, user_id, strokes):
    """
    Insert data into `wm_strokes_to_symbol`.

    Parameters
    ----------
    raw_data_id : int
    user_id : int
    strokes: list of int
    """
    cfg = utils.get_database_configuration()
    mysql = cfg['mysql_dev']
    connection = pymysql.connect(host=mysql['host'],
                                 user=mysql['user'],
                                 passwd=mysql['passwd'],
                                 db=mysql['db'],
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    cursor = connection.cursor()
    sql = ("INSERT INTO `wm_partial_answer` "
           "(`recording_id`, `symbol_id`, `strokes`, `user_id`, `is_accepted`) "
           "VALUES (%s, %s, %s, %s, 1);")
    data = (raw_data_id,
            symbol_id,
            ",".join([str(stroke) for stroke in strokes]),
            user_id)
    cursor.execute(sql, data)
    connection.commit()
