#!/usr/bin/env python

import logging
import sys
import datetime

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)

from hwrt.datasets import inkml


def main(directory):
    recordings = inkml.read_folder(directory)
    for hw in recordings:
        hw.creation_date = datetime.datetime.fromtimestamp(hw.get_sorted_pointlist()[0][0]['time']/1000.0)
        print(hw.creation_date)


if __name__ == '__main__':
    main("/home/moose/Downloads/expressmatch-time-datasetV0.2")
