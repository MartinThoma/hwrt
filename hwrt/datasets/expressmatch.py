#!/usr/bin/env python

import logging
import sys
import datetime

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)

import os

from hwrt.datasets import inkml
from hwrt.datasets import getuserid, insert_recording


def main(directory):
    recordings = inkml.read_folder(directory)
    for hw in recordings:
        hw.creation_date = datetime.datetime.fromtimestamp(hw.get_sorted_pointlist()[0][0]['time']/1000.0)
        hw.internal_id = hw.filepath
        # username
        username = os.path.basename(hw.filepath)
        username = username.split('_')[1]
        username = username.split('.')[0]
        hw.username = "expressmatch::%s" % username
        print(hw.username)
        # insert user
        copyright_str = ("This dataset was contributed by "
                         "[express-match](https://code.google.com/p/express-match/)."
                         "It is described in the paper "
                         "'ExpressMatch: A System for Creating Ground-Truthed "
                         "Datasets of Online Mathematical Expressions'.")
        hw.user_id = getuserid(hw.username, copyright_str)
        # insert recording
        insert_recording(hw)
        print(hw.symbol_stream)
        print(hw.segmentation)
        #hw.show()


if __name__ == '__main__':
    main("/home/moose/Downloads/expressmatch-time-datasetV0.2")
