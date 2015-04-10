#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Create a complete strucutre dump of the database."""

from __future__ import unicode_literals
import logging
import sys
PY3 = sys.version > '3'

if not PY3:
    from future.builtins import open
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.INFO,
                    stream=sys.stdout)

import pymysql
import re
from natsort import natsorted
import binascii

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
    """Dump the structure (including constraints) of the database.

    Parameters
    ----------
    mysql_cfg : dict
        Database credentials
    prefix : str, optional
        Only make a backup of tables with this prefix
    fetch_data : boolean, optional
        Make a backup of the data, too
    filename_strucutre : str, optional
        Name of the file which will contain the structure of the database
    filename_constraints : str, optional
        Name of the file which will contain the constraints

    Returns
    -------
    list
        Names of the tables
    """
    import datetime
    now = datetime.datetime.now()
    formatted_time = now.strftime("%Y-%m-%d_%H-%M")
    if filename_strucutre is None:
        filename_strucutre = "backup_structure_%s.sql" % formatted_time
    if filename_constraints is None:
        filename_constraints = "backup_constraints_%s.sql" % formatted_time
    connection = pymysql.connect(host=mysql_cfg['host'],
                                 user=mysql_cfg['user'],
                                 passwd=mysql_cfg['passwd'],
                                 db=mysql_cfg['db'],
                                 charset='utf8')
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
            data += "-- " + "-"*56 + "\n\n"
            data += "--\n"
            data += u"-- Tabellenstruktur für Tabelle `%s`\n" % table_name
            data += "--\n"
            cursor.execute("SHOW CREATE TABLE `%s`" % table_name)
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
        pattern = re.compile(",\n\)")
        data = pattern.sub("\n)", data)
        with open(filename_strucutre, "wb") as f:
            f.write(data.encode("utf-8"))
        with open(filename_constraints, "wb") as f:
            f.write(constraint_data.encode("utf-8"))
        cursor.close()
    finally:
        connection.close()
    return tables


def db_dump_table(mysql_cfg, table_name, filename):
    """Dump a single table."""
    connection = pymysql.connect(host=mysql_cfg['host'],
                                 user=mysql_cfg['user'],
                                 passwd=mysql_cfg['passwd'],
                                 db=mysql_cfg['db'],
                                 charset='utf8')
    data = ""
    data += "SET SQL_MODE=\"NO_AUTO_VALUE_ON_ZERO\";\n"
    data += "SET time_zone = \"+00:00\";\n\n"
    data += "--\n"
    data += "-- Datenbank: `%s`\n" % mysql_cfg['db']
    data += "--\n"
    data += "\n"
    data += "--\n"
    data += u"-- Daten für Tabelle `%s`\n" % table_name
    data += "--\n"

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM %s;" % table_name)
        rows = None
        datasets = cursor.fetchall()
        last = len(datasets) - 1
        chunking_threshold = 957
        for counter, row in enumerate(datasets):
            if rows is None:
                rows = "(`%s`)" % "`, `".join([r[0] for r in cursor.description])
            if counter % chunking_threshold == 0:
                data += "\nINSERT INTO `%s` %s VALUES\n" % (table_name, str(rows))
            data += "("
            first = True
            for i, field in enumerate(row):
                if not first:
                    data += ', '
                if cursor.description[i][1] == 3:  # type is int
                    data += u"%s" % str(field)
                elif cursor.description[i][1] == 252:  # type textfield
                    try:
                        data += "0x%s" % binascii.hexlify(field)
                    except Exception as inst:
                        data += u"'{0}'".format(field)
                else:
                    # print(type(field))
                    # print(field)
                    # print(cursor.description[i][1])
                    data += u"'{0}'".format(field)
                first = False
            if counter == last:
                data += ");\n"
            else:
                data += "),\n"
            if counter + 1 % chunking_threshold == 0:
                data += ");\n"
        data += "\n\n"
        if len(datasets) > 0:
            with open(filename, "wb") as f:
                f.write(data.encode("utf-8"))
    finally:
        connection.close()


def main():
    cfg = utils.get_database_configuration()
    mysql = cfg['mysql_online']
    logging.info("Start dumping structure and constraints...")
    dir_s = "/home/moose/GitHub/write-math"
    tables = dump_structure(mysql,
                            prefix='wm_',
                            filename_strucutre="%s/database/structure/write-math.sql" % dir_s,
                            filename_constraints="%s/database/structure/foreign-keys.sql" % dir_s)
    # for table_name in tables:
    #     if "raw_draw_data" not in table_name:
    #         #if "wm_languages" == table_name:
    #         logging.info("Dump table '%s'...", table_name)
    #         path = os.path.join("%s/database/complete-dump/single_tables_1/%s.sql" % (dir_s, table_name))
    #         db_dump_table(mysql, table_name, path)

if __name__ == '__main__':
    main()
