"""
Check if data files are here and which version they have.

Contact the server for the latest version and update them if they are outdated.
"""

# Core Library modules
import hashlib
import logging
import os
import urllib.request

# Third party modules
import yaml

# Local modules
from . import utils

logger = logging.getLogger(__name__)


def generate_file_md5(local_path_file, blocksize=2 ** 20):
    # http://stackoverflow.com/a/1131255/3345926
    file_hash = hashlib.md5()
    with open(local_path_file, "rb") as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            file_hash.update(buf)
    return file_hash.hexdigest()


def is_file_consistent(local_path_file, md5_hash):
    """Check if file is there and if the md5_hash is correct."""
    return (
        os.path.isfile(local_path_file)
        and generate_file_md5(local_path_file) == md5_hash
    )


def main():
    """Main part of the download script."""
    # Read config file. This has to get updated via git
    project_root = utils.get_project_root()
    infofile = os.path.join(project_root, "raw-datasets/info.yml")
    logger.info("Read '%s'...", infofile)
    with open(infofile) as ymlfile:
        datasets = yaml.safe_load(ymlfile)
    for dataset in datasets:
        local_path_file = os.path.join(project_root, dataset["online_path"])
        i = 0
        while not is_file_consistent(local_path_file, dataset["md5"]) and i < 3:
            if os.path.isfile(local_path_file):
                local_file_size = os.path.getsize(local_path_file)
                logger.info("MD5 codes differ. ")
                logger.info(
                    "The file size of the downloaded file is %s.",
                    utils.sizeof_fmt(local_file_size),
                )
            logger.info("Download the file '%s'...", dataset["online_path"])
            urllib.request.urlretrieve(dataset["url"], local_path_file)
            i += 1
        if i < 10:
            logger.info("Found '%s'.", dataset["online_path"])
