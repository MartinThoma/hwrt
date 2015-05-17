#!/usr/bin/env python

"""
Normalize the data in `wm_formula`.`formula_in_latex`

This is only useful for write-math.com
"""

import pymysql
import pymysql.cursors

# hwrt modules
from hwrt.HandwrittenData import HandwrittenData
import hwrt.latex as latex
import hwrt.utils as utils


def main(mysql):
    connection = pymysql.connect(host=mysql['host'],
                                 user=mysql['user'],
                                 passwd=mysql['passwd'],
                                 db=mysql['db'],
                                 cursorclass=pymysql.cursors.DictCursor)
    cursor = connection.cursor()

    # Download all formula_in_latex
    sql = "SELECT `id`, `formula_in_latex` FROM `wm_formula` "
    cursor.execute(sql)
    datasets = cursor.fetchall()

    j = 1

    latex2id = {}
    for data in datasets:
        fid, formula_in_latex = data['id'], data['formula_in_latex']
        latex2id[formula_in_latex] = fid

    for i, data in enumerate(datasets, start=1433):
        fid, formula_in_latex = data['id'], data['formula_in_latex']
        latex2id[formula_in_latex] = fid
        if latex.normalize(formula_in_latex) in latex2id:
            newid = latex2id[latex.normalize(formula_in_latex)]
        else:
            newid = 0
        if latex.normalize(formula_in_latex) != formula_in_latex:
            print("## %i (%i -> %i)" % (j, fid, newid))
            print("\t%s changes to" % formula_in_latex)
            print("\t%s" % latex.normalize(formula_in_latex))
            if newid == 0:
                print("\tNo collision: Change automatically")
                sql = ("UPDATE `wm_formula` "
                       "SET `formula_in_latex` = %s, "
                       "`formula_name` = %s "
                       "WHERE  `wm_formula`.`id` = %s LIMIT 1;")
                cursor.execute(sql, (latex.normalize(formula_in_latex),
                                     latex.normalize(formula_in_latex),
                                     fid))
                connection.commit()
            j += 1
        if j > 20:
            # Make sure not too much gets messed up if something goes wrong
            break


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
    # if 'mysql_local' in cfg:
    #     main(cfg['mysql_local'])
