#!/usr/bin/env python

"""Check if data files are here and which version they have. Contact the
   server for the latest version and update them if they are outdated.
"""

import sys
import os
import logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)
import yaml
import hashlib
import urllib
# my ones
import hwrt.utils as utils


def is_file_consistent(local_path_file, md5_hash):
    """Check if file is there and if the md5_hash is correct."""
    if not os.path.isfile(local_path_file):
        return False
    if hashlib.md5(open(local_path_file, 'rb').read()).hexdigest() != md5_hash:
        return False
    return True


def get_parser():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    return parser


def main():
    # Read config file. This has to get updated via git
    PROJECT_ROOT = utils.get_project_root()
    infofile = os.path.join(PROJECT_ROOT, "raw-datasets/info.yml")
    logging.info("Read '%s'...", infofile)
    with open(infofile, 'r') as ymlfile:
        datasets = yaml.load(ymlfile)
    for dataset in datasets:
        local_path_file = os.path.join(PROJECT_ROOT, dataset['online_path'])
        i = 0
        while not is_file_consistent(local_path_file, dataset['md5']) and i < 3:
            if os.path.isfile(local_path_file):
                logging.info("MD5 codes differ. ")
                logging.info("The file size of the downloaded file is %s." %
                             utils.sizeof_fmt(os.path.getsize(local_path_file))
                             )
            logging.info("Download the file '%s'...", dataset['online_path'])
            urllib.urlretrieve(dataset['url'], local_path_file)
            i += 1
        if i < 10:
            logging.info("Found '%s'.", dataset['online_path'])


if __name__ == "__main__":
    get_parser().parse_args()
    main()
