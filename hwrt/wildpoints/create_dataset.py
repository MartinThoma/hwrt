#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Download data from the server to create a dataset which consists of recordings
of symbols with dots and recordings with WILDPOINTs.
"""

# Inspired by "backup.py"

import pymysql.cursors
import logging
import sys
import pickle
import json

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)

# hwrt modules
from hwrt.handwritten_data import HandwrittenData
from hwrt import utils
from hwrt import segmentation


def main():
    symbol_ids = get_symbol_ids_with_dots()
    recordings = download_recordings(symbol_ids)
    logging.info("Got %i recordings. Pickle them...", len(recordings))
    with open("wildpoint-data.pickle", "wb") as handle:
        pickle.dump(recordings, handle, 2)


def get_symbol_ids_with_dots():
    """
    Get a list of all symbol ids on write-math.com which have dots.

    Returns
    -------
    list of ints
        A list of IDs of symbols which have a dot.
    """
    # Get cursor
    mysql = utils.get_mysql_cfg()
    connection = pymysql.connect(host=mysql['host'],
                                 user=mysql['user'],
                                 passwd=mysql['passwd'],
                                 db=mysql['db'],
                                 cursorclass=pymysql.cursors.DictCursor)
    cursor = connection.cursor()

    # Do stuff
    sql = "SELECT `id` FROM `wm_tags` WHERE `tag_name` = 'has-dot'"
    cursor.execute(sql)
    has_dots_id = cursor.fetchone()['id']
    sql = ("SELECT `symbol_id` FROM `wm_tags2symbols` "
           "WHERE tag_id = %s "
           "ORDER BY `symbol_id` ASC")
    cursor.execute(sql, (has_dots_id, ))
    formulas = [el['symbol_id'] for el in cursor.fetchall()]
    logging.info("Fetched %i symbol-ids with the tag 'has-dot'.",
                 len(formulas))
    return formulas


def download_recordings(symbol_ids):
    """
    Download all recordings which either might have a dot because their
    corresponding symbol has a dot (e.g. i, j) or because the recording has a
    WILDPOINT.

    Parameters
    ----------
    symbol_ids : list of ints
        Download all recordings of those symbols as they might have dots
    """
    recordings = []
    known_ids = set()

    # Get cursor
    mysql = utils.get_mysql_cfg()
    connection = pymysql.connect(host=mysql['host'],
                                 user=mysql['user'],
                                 passwd=mysql['passwd'],
                                 db=mysql['db'],
                                 cursorclass=pymysql.cursors.DictCursor)
    cursor = connection.cursor()

    # Download recordings of symbols with dots
    for i, symbol_id in enumerate(symbol_ids, start=1):
        logging.info("%i: Download recordings of symbol with ID %i",
                     i, symbol_id)
        sql = ("SELECT id, data, wild_point_count, missing_line, user_id, "
               "segmentation, nr_of_symbols "
               "FROM `wm_raw_draw_data` "
               "WHERE accepted_formula_id=%s "
               "AND no_geometry=0 AND classifiable=1 "
               "AND accepted_formula_id!=1")
        cursor.execute(sql, (symbol_id, ))
        datasets = cursor.fetchall()
        for raw_data in datasets:
            seg = raw_data['segmentation']
            if seg is not None:
                seg = json.loads(raw_data['segmentation'])
            handwriting = HandwrittenData(raw_data['data'],
                                          symbol_id,  # formula['id'],
                                          raw_data['id'],
                                          '',  # formula['formula_in_latex'],
                                          raw_data['wild_point_count'],
                                          raw_data['missing_line'],
                                          raw_data['user_id'],
                                          segmentation=seg)
            handwriting.ann_segmentation = get_ann_segmentation(handwriting)
            handwriting.nr_of_symbols = raw_data['nr_of_symbols']
            recordings.append(handwriting)
            known_ids.add(raw_data['id'])
            is_segmentation_ok(handwriting)
    logging.info("Got %i recordings.", len(recordings))

    # Download recordings which have a wild point
    # Ideas:
    # - Limit this to the number of recordings got so far to prevent
    #   overfitting?
    # - Only take recordings with have not too many WILDPOINTs?
    logging.info("Start downloading recordings with WILDPOINTs")
    sql = ("SELECT id, data, wild_point_count, missing_line, user_id, "
           "segmentation, nr_of_symbols "
           "FROM `wm_raw_draw_data` "
           "WHERE wild_point_count > 0 "
           "AND no_geometry=0 AND classifiable=1 "
           "AND accepted_formula_id!=1")
    cursor.execute(sql)
    datasets = cursor.fetchall()
    for raw_data in datasets:
        if raw_data['id'] not in known_ids:
            handwriting = HandwrittenData(raw_data['data'],
                                          symbol_id,  # formula['id'],
                                          raw_data['id'],
                                          '',  # formula['formula_in_latex'],
                                          raw_data['wild_point_count'],
                                          raw_data['missing_line'],
                                          raw_data['user_id'])
            if raw_data['wild_point_count'] > 3:
                logging.warning("Recording '%i' has %i WILDPOINTs",
                                raw_data['id'],
                                raw_data['wild_point_count'])
            handwriting.ann_segmentation = get_ann_segmentation(handwriting)
            handwriting.nr_of_symbols = raw_data['nr_of_symbols']
            recordings.append(handwriting)
            known_ids.add(raw_data['id'])
            is_segmentation_ok(handwriting)
    return recordings


def get_ann_segmentation(hw):
    """Get annotated segmentation.

    Return a dictionary with the keys 'segmentation' and 'symbol-ids', where
    'segmentation' contains a list of lists (e.g. [[0, 1], [2, 3, 4]] meaning
    the first two strokes are part of one symbol and the strokes 2, 3 and 4
    are part of another symobl) and 'symbol-ids' is a list of the same length
    as 'segmentation', but with symbol ids (e.g. [42, 1337], meaning that the
    first symbol in the segmentation is the symbol with the id 42 and the
    second one is the symbol with ID 1337).
    """

    # Get cursor
    mysql = utils.get_mysql_cfg()
    connection = pymysql.connect(host=mysql['host'],
                                 user=mysql['user'],
                                 passwd=mysql['passwd'],
                                 db=mysql['db'],
                                 cursorclass=pymysql.cursors.DictCursor)
    cursor = connection.cursor()

    # Get partial answers
    sql = ("SELECT `strokes`, `symbol_id` FROM  `wm_partial_answer` "
           "WHERE is_accepted=1 AND recording_id=%s")
    cursor.execute(sql, (hw.raw_data_id, ))
    partial_answers = cursor.fetchall()

    # Normalize partial answers
    for i in range(len(partial_answers)):
        stroke_list = partial_answers[i]['strokes'].split(',')
        partial_answers[i]['strokes'] = [int(stroke) for stroke in stroke_list]
        partial_answers[i]['strokes'] = sorted(partial_answers[i]['strokes'])

    stroke_nr = len(hw.get_sorted_pointlist())

    if len(hw.segmentation) > 0:
        symbol_ids = [None for i in range(len(hw.segmentation))]
        # The hw has a segmentation
        hw.segmentation = segmentation.normalize_segmentation(hw.segmentation)
        if len(partial_answers) > 0:
            for pa in partial_answers:
                if len(pa['strokes']) == stroke_nr:
                    symbol_ids = [pa['symbol_id']]
                    hw.segmentation = [pa['strokes']]
                elif pa['strokes'] not in hw.segmentation:
                    logging.warning(("http://write-math.com/view/"
                                     "?raw_data_id=%i "
                                     "has a segmentation, but it does not "
                                     "match the accepted answers."),
                                    hw.raw_data_id)
                    logging.warning("hw.segmentation=%s", str(hw.segmentation))
                    logging.warning("partial_answers=%s", str(partial_answers))
                else:
                    symbol_ids[hw.segmentation.index(pa['strokes'])] = \
                        pa['symbol_id']
        elif len(hw.segmentation) == 1:
            symbol_ids = [hw.formula_id]
        if symbol_ids.count(None) > 0:
            logging.warning(("http://write-math.com/view/?raw_data_id=%i "
                             "has a segmentation=%s and partial answers=%s, "
                             "but not every stroke is classified by now:%s"),
                            hw.raw_data_id,
                            hw.segmentation,
                            partial_answers,
                            symbol_ids)
    else:
        hw.segmentation = [[i for i in range(stroke_nr)]]
        symbol_ids = [hw.formula_id]
        # The hw has no segmentation
        if hw.wild_point_count > 0:
            logging.info(("http://write-math.com/view/?raw_data_id=%i "
                          "has no segmentation, but WILDPOINTs."),
                         hw.raw_data_id)
        elif len(partial_answers) > 0:
            logging.info(("http://write-math.com/view/?raw_data_id=%i "
                          "has no segmentation, but partial answers."),
                         hw.raw_data_id)
        else:
            pass

    return {'segmentation': hw.segmentation,
            'symbol-ids': symbol_ids}


def is_segmentation_ok(hw):
    if hw.nr_of_symbols <= hw.wild_point_count:
        logging.info(("http://write-math.com/view/?raw_data_id=%i "
                      "hw.nr_of_symbols <= hw.wild_point_count"),
                     hw.raw_data_id)
        return False
    if hw.nr_of_symbols != len(hw.segmentation):
        logging.info(("http://write-math.com/view/?raw_data_id=%i "
                      "hw.nr_of_symbols = %i != %i = len(hw.segmentation):%s"),
                     hw.raw_data_id,
                     hw.nr_of_symbols,
                     len(hw.segmentation),
                     str(hw.segmentation))
        return False
    return True


def get_parser():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    return parser


if __name__ == "__main__":
    args = get_parser().parse_args()
    main()
