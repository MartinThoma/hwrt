#!/usr/bin/env python

"""Script to import data into write-math.com"""

import logging
import sys

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)

# hwrt modules
from hwrt.datasets import mfrdb
from hwrt import datasets


def main(directory):
    recordings = mfrdb.get_recordings(directory)
    logging.info("Got recordings for %i symbols.", len(recordings))
    recordings = sorted(recordings, key=lambda n: len(n[1]))
    for symbol, symbol_recs in recordings:
        logging.info("{0:>10}: {1} recordings".format(symbol,
                                                      len(symbol_recs)))
        for hw, info in symbol_recs:
            pass
            #datasets.insert_recording(hw, info)
    logging.info("Done importing dataset")


if __name__ == '__main__':
    main("/home/moose/Downloads/MfrDB_Symbols_v1.0")
