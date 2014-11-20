#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Check if data files are here and which version they have. Contact the
   server for the latest version and update them if they are outdated.
"""

import logging
import os
import yaml
import hashlib
import urllib

# hwrt modules
import hwrt.utils as utils


def is_file_consistent(local_path_file, md5_hash):
    """Check if file is there and if the md5_hash is correct."""
    return os.path.isfile(local_path_file) and \
        hashlib.md5(open(local_path_file, 'rb').read()).hexdigest() == md5_hash


def get_parser():
    """Return the parser object for this script."""
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    return parser


def main():
    """Main part of the download script."""
    # Read config file. This has to get updated via git
    project_root = utils.get_project_root()
    infofile = os.path.join(project_root, "raw-datasets/info.yml")
    logging.info("Read '%s'...", infofile)
    with open(infofile, 'r') as ymlfile:
        datasets = yaml.load(ymlfile)
    for dataset in datasets:
        local_path_file = os.path.join(project_root, dataset['online_path'])
        i = 0
        while not is_file_consistent(local_path_file, dataset['md5']) and i < 3:
            if os.path.isfile(local_path_file):
                local_file_size = os.path.getsize(local_path_file)
                logging.info("MD5 codes differ. ")
                logging.info("The file size of the downloaded file is %s.",
                             utils.sizeof_fmt(local_file_size))
            logging.info("Download the file '%s'...", dataset['online_path'])
            urllib.urlretrieve(dataset['url'], local_path_file)
            i += 1
        if i < 10:
            logging.info("Found '%s'.", dataset['online_path'])


if __name__ == "__main__":
    get_parser().parse_args()
    main()
