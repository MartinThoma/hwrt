#!/usr/bin/env python

"""Evaluate data."""

import logging
import sys
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s",
                    level=logging.DEBUG,
                    stream=sys.stdout)
import yaml
import json
# mine
import hwrt.utils as utils


def main(model_folder, output_format, n):
    recording = sys.stdin.readline()
    raw_data_json = json.dumps(yaml.load(recording))
    logging.info(recording)
    logging.info("Start evaluation...")
    results = utils.classify_single_recording(raw_data_json, model_folder)
    for latex, probability in results:
        if n == 0:
            break
        else:
            n -= 1
        print("{0:15s} {1:5f}".format(latex, probability))


def get_parser():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-m", "--model",
                        dest="model",
                        help="where is the model folder (with a info.yml)?",
                        metavar="FOLDER",
                        type=lambda x: utils.is_valid_folder(parser, x),
                        default=utils.default_model())
    parser.add_argument("--output-format",
                        dest="output_format",
                        help="in which format should the output be",
                        choices=["csv", "human-readable"],
                        default="human-readable")
    parser.add_argument("-n",
                        dest="n", default=10, type=int,
                        help="Show TOP-N results")
    return parser

if __name__ == "__main__":
    args = get_parser().parse_args()
    main(args.model, args.output_format, args.n)
