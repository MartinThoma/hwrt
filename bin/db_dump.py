#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Create a complete strucutre dump of the database."""

import logging
import sys
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.INFO,
                    stream=sys.stdout)
try:  # Python 2
    import cPickle as pickle
except ImportError:  # Python 3
    import pickle

import pymysql
import re
from natsort import natsorted

# hwrt modules
import hwrt.utils as utils


def get_constraind_str(creation_str, table_name):
    constr = "--\n"
    constr += "-- Constraints der Tabelle `%s`\n" % table_name
    constr += "--\n"
    constr += "ALTER TABLE `%s`\n" % table_name
    pattern = re.compile(r'(?m)^  CONSTRAINT.*\n?')
    matches = pattern.findall(creation_str)
    if len(matches) == 0:
        return ""
    for m in matches:
        constr += "  ADD %s\n" % m.strip()
    constr = constr.strip()
    constr += ";\n\n"
    return constr


def dump_structure(mysql_cfg,
                   prefix=None,
                   fetch_data=False,
                   filename_strucutre=None,
                   filename_constraints=None):
    if filename_strucutre is None:
        import datetime
        now = datetime.datetime.now()
        filename_strucutre = "backup_structure_%s.sql" % now.strftime("%Y-%m-%d_%H-%M")
    if filename_constraints is None:
        import datetime
        now = datetime.datetime.now()
        filename_constraints = "backup_constraints_%s.sql" % now.strftime("%Y-%m-%d_%H-%M")
    connection = pymysql.connect(host=mysql_cfg['host'],
                                 user=mysql_cfg['user'],
                                 passwd=mysql_cfg['passwd'],
                                 db=mysql_cfg['db'])
    tables = []
    constraint_data = "--\n"
    constraint_data += "-- Constraints der exportierten Tabellen\n"
    constraint_data += "--\n\n"
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        for table in cursor.fetchall():
            table_name = table[0]
            if prefix is None or table_name.startswith(prefix):
                tables.append(table_name)
        tables = natsorted(tables)
        # cursor.execute("use INFORMATION_SCHEMA;")
        data = "--\n"
        data += "-- Datenbank: `%s`\n" % mysql_cfg['db']
        data += "--\n\n"
        for table_name in tables:
            #data += "DROP TABLE IF EXISTS `%s`;" % table_name
            data += "-- " + "-"*56 + "\n\n"
            data += "--\n"
            data += "-- Tabellenstruktur für Tabelle `%s`\n" % table_name
            data += "--\n"
            cursor.execute("SHOW CREATE TABLE `%s`" % table_name)
            # cursor.execute(("select TABLE_NAME,COLUMN_NAME,CONSTRAINT_NAME, "
            #                 "REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME from KEY_COLUMN_USAGE "
            #                 "where TABLE_SCHEMA = '%s' and TABLE_NAME = '%s'") % (mysql_cfg['db'], table_name))
            table_structure = cursor.fetchone()[1]
            table_structure = table_structure.replace("CREATE TABLE ", "CREATE TABLE IF NOT EXISTS ")

            constraint_data += get_constraind_str(table_structure, table_name)

            pattern = re.compile(r'(?m)^  CONSTRAINT.*\n?')
            table_structure = pattern.sub('', table_structure)
            data += "\n%s;\n\n" % table_structure

            if fetch_data:
                cursor.execute("SELECT * FROM %s;", (table_name, ))
                for row in cursor.fetchall():
                    data += "INSERT INTO `%s` VALUES(" % table_name
                    first = True
                    for field in row:
                        if not first:
                            data += ', '
                        data += '"' + str(field) + '"'
                        first = False

                    data += ");\n"
                data += "\n\n"

        with open(filename_strucutre, "w") as f:
            f.writelines(data)
        with open(filename_constraints, "w") as f:
            f.writelines(constraint_data)
        cursor.close()
    finally:
        connection.close()


def main():
    cfg = utils.get_database_configuration()
    mysql = cfg['mysql_online']
    dump_structure(mysql,
                   prefix='wm_',
                   filename_strucutre="/home/moose/GitHub/write-math/database/structure/write-math.sql",
                   filename_constraints="/home/moose/GitHub/write-math/database/structure/foreign-keys.sql")

if __name__ == '__main__':
    main()
