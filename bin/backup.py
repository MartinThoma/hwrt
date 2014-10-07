#!/usr/bin/env python
"""
Download raw data from online server and back it up (e.g. on dropbox)
handwriting_datasets.pickle.
"""

import logging
import sys
import os
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.INFO,
                    stream=sys.stdout)
import cPickle as pickle
import MySQLdb
import MySQLdb.cursors
import dropbox
import hashlib
import webbrowser
import yaml
import time
# mine
from hwrt.HandwrittenData import HandwrittenData
import hwrt.utils as utils


def input_string(question=""):
    """A function that works for both, Python 2.x and Python 3.x.
       It asks the user for input and returns it as a string.
    """
    import sys
    if sys.version_info[0] == 2:
        return raw_input(question)
    else:
        return input(question)


def check_dropbox():
    """Check if the dropbox signin data is correct."""
    cfg = utils.get_project_configuration()
    if 'dropbox_app_key' not in cfg:
        logging.error("'dropbox_app_key' was not found.")
        return False
    elif 'dropbox_app_secret' not in cfg:
        logging.error("'dropbox_app_key' was not found.")
        return False
    else:
        return True


def dropbox_upload(filename, directory, client):
    local_path = os.path.join(utils.get_project_root(), directory, filename)
    online_path = os.path.join(directory, filename)
    filesize = os.path.getsize(local_path)
    logging.info("Start uploading '%s' (%s)...",
                 filename,
                 utils.sizeof_fmt(filesize))
    f = open(local_path, 'rb')
    uploader = client.get_chunked_uploader(f, filesize)
    uploader.upload_chunked()
    uploader.finish(online_path, overwrite=True)
    url = client.share(online_path,
                       short_url=False)['url'].encode('ascii', 'ignore')
    url = url.replace("?dl=0", "?dl=1")
    return url


def sync_directory(directory):
    """Sync a directory. Return if syncing was successful."""
    # Developers should read
    # https://www.dropbox.com/developers/core/start/python
    # before modifying the following code
    cfg = utils.get_project_configuration()

    # Information about files in this folder
    PROJECT_ROOT = utils.get_project_root()
    directory_information_file = os.path.join(PROJECT_ROOT,
                                              directory, "info.yml")
    if not os.path.isfile(directory_information_file):  # create if not exists
        with open(directory_information_file, 'w') as ymlfile:
            ymlfile.write(yaml.dump([]))

    # Dropbox stuff
    APP_KEY = cfg['dropbox_app_key']
    APP_SECRET = cfg['dropbox_app_secret']

    flow = dropbox.client.DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET)
    authorize_url = flow.start()
    webbrowser.open_new_tab(authorize_url)
    print("1. Go to: " + authorize_url)
    print("2. Click 'Allow' (you might have to log in first)")
    print("3. Copy the authorization code.")
    access_token = input_string().strip()

    try:
        # This will fail if the user enters an invalid authorization code
        access_token, user_id = flow.finish(access_token)
        client = dropbox.client.DropboxClient(access_token)
    except Exception as e:
        logging.error("Dropbox connection error: %s", e)
        return False

    # Get all local files
    local_path = os.path.join(PROJECT_ROOT, directory)
    files = [f for f in os.listdir(local_path)
             if os.path.isfile(os.path.join(local_path, f))]
    files = filter(lambda n: n.endswith(".pickle"), files)

    new_yaml_content = []

    # upload them
    for filename in files:
        file_meta = {}
        file_meta['filename'] = filename
        file_meta['online_path'] = os.path.join(directory, filename)
        local_path_file = os.path.join(local_path, filename)
        file_meta['md5'] = hashlib.md5(open(local_path_file,
                                            'rb').read()).hexdigest()
        new_yaml_content.append(file_meta)
        file_meta['url'] = dropbox_upload(filename, directory, client)
        if not file_meta['url']:
            return False

    # TODO: Remove all files from Dropbox that are not in local folder

    # Update YAML file
    with open(directory_information_file, 'w') as ymlfile:
        ymlfile.write(yaml.dump(new_yaml_content, default_flow_style=False))

    return True


def main(destination=os.path.join(utils.get_project_root(),
                                  "archive/raw-datasets"),
         small_dataset=False):
    time_prefix = time.strftime("%Y-%m-%d-%H-%M")
    if small_dataset:
        filename = "%s-handwriting_datasets-small-raw.pickle" % time_prefix
    else:
        filename = "%s-handwriting_datasets-raw.pickle" % time_prefix
    destination_path = os.path.join(destination, filename)
    logging.info("Data will be written to '%s'" % destination_path)
    cfg = utils.get_database_configuration()
    mysql = cfg['mysql_online']
    connection = MySQLdb.connect(host=mysql['host'],
                                 user=mysql['user'],
                                 passwd=mysql['passwd'],
                                 db=mysql['db'],
                                 cursorclass=MySQLdb.cursors.DictCursor)
    cursor = connection.cursor()

    # Get all formulas that should get examined
    if small_dataset:
        sql = ("SELECT `id`, `formula_in_latex` FROM `wm_formula` "
               # only use the important symbol subset
               "WHERE `is_important` = 1 "
               "AND id != 1 "  # exclude trash class
               "AND id <= 81 "
               "ORDER BY `id` ASC")
    else:
        sql = ("SELECT `id`, `formula_in_latex` FROM `wm_formula` "
               # only use the important symbol subset
               "WHERE `is_important` = 1 "
               "AND id != 1 "  # exclude trash class
               "ORDER BY `id` ASC")
    cursor.execute(sql)
    formulas = cursor.fetchall()

    handwriting_datasets = []
    formula_id2latex = {}

    # Go through each formula and download every raw_data instance
    for formula in formulas:
        formula_id2latex[formula['id']] = formula['formula_in_latex']
        sql = ("SELECT `id`, `data`, `is_in_testset`, `wild_point_count`, "
               "`missing_line`, `user_id` "
               "FROM `wm_raw_draw_data` "
               "WHERE `accepted_formula_id` = %s" % str(formula['id']))
        cursor.execute(sql)
        raw_datasets = cursor.fetchall()
        logging.info("%s (%i)" % (formula['formula_in_latex'],
                                  len(raw_datasets)))
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
                                             'id': raw_data['id'],
                                             'formula_id': formula['id'],
                                             'formula_in_latex':
                                             formula['formula_in_latex'],
                                             'is_in_testset':
                                             raw_data['is_in_testset']
                                             })
            except Exception as e:
                logging.info("Raw data id: %s" % raw_data['id'])
                logging.info(e)
    pickle.dump({'handwriting_datasets': handwriting_datasets,
                 'formula_id2latex': formula_id2latex,
                 },
                open(destination_path, "wb"),
                2)


if __name__ == '__main__':
    PROJECT_ROOT = utils.get_project_root()
    archive_path = os.path.join(PROJECT_ROOT, "archive/raw-datasets")
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--destination", dest="destination",
                        default=archive_path,
                        help="where do write the handwriting_dataset.pickle",
                        type=lambda x: utils.is_valid_file(parser, x),
                        metavar="FOLDER")
    parser.add_argument("-s", "--small", dest="small",
                        action="store_true", default=False,
                        help=("should only a small dataset (with all capital "
                              "letters) be created?"))
    parser.add_argument("-o", "--onlydropbox", dest="onlydropbox",
                        action="store_true", default=False,
                        help=("don't download new files; only upload to "
                              "dropbox"))
    args = parser.parse_args()

    logging.info("Don't forget to run 'create_testset_online_once.py'.")

    if not check_dropbox():
        logging.error("Dropbox login data was not correct. "
                      "Please check your '~/.writemathrc' file.")
    else:
        if not args.onlydropbox:
            main(args.destination, args.small)
        if sync_directory("archive/raw-datasets"):
            logging.info("Successfully uploaded files to Dropbox.")
        else:
            logging.info("Uploading files to Dropbox failed.")
