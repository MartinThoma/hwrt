#!/usr/bin/env python

"""Testing script for write-math symbol classifier."""

# Core Library modules
import json
import logging
import sys

# Third party modules
import numpy

# Local modules
from ..classify import classify_segmented_recording as evaluate
from ..datasets import mfrdb
from ..utils import less_than

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.DEBUG,
    stream=sys.stdout,
)


def main(directory):
    recordings = mfrdb.get_recordings(directory)
    print(len(recordings))

    score_place = []
    symbols_showed = []
    for latex, symbol_recording in recordings:
        score_place_symbol = []
        for recording in symbol_recording:
            results = evaluate(
                json.dumps(recording.get_sorted_pointlist()), result_format="LaTeX"
            )
            for i, result in enumerate(results):
                if result["semantics"] == recording.formula_in_latex:
                    # if i > 5:
                    #     logging.info("  Found '%s' place %i with probability %0.4f.",
                    #                  recording.formula_in_latex,
                    #                  i,
                    #                  result['probability'])
                    #     if recording.formula_in_latex not in symbols_showed:
                    #         #recording.show()
                    #         symbols_showed.append(recording.formula_in_latex)
                    score_place.append(i)
                    score_place_symbol.append(i)
                    break
            else:
                if recording.formula_in_latex not in symbols_showed:
                    logging.info("#" * 80)
                    logging.info(recording.formula_in_latex)
                    symbols_showed.append(recording.formula_in_latex)
        logging.info(
            (
                "{:>10}: TOP-1: {:0.2f} | TOP-3: {:0.2f} | "
                "TOP-10: {:0.2f} | TOP-50: {:0.2f} | {}"
            ).format(
                latex,
                less_than(score_place_symbol, 1) / len(symbol_recording),
                less_than(score_place_symbol, 3) / len(symbol_recording),
                less_than(score_place_symbol, 10) / len(symbol_recording),
                less_than(score_place_symbol, 50) / len(symbol_recording),
                len(symbol_recording),
            )
        )

    total_recordings = len([1 for l, symb in recordings for el in symb])
    logging.info("mean place of correct classification: %0.2f", numpy.mean(score_place))
    logging.info(
        "median place of correct classification: %0.2f", numpy.median(score_place)
    )
    for i in [1, 3, 10, 20, 50]:
        logging.info(
            "TOP-%i: %0.2f correct", i, less_than(score_place, i) / total_recordings
        )
    # logging.info("Out of order: %i", out_of_order_count)
    logging.info("Total: %i", total_recordings)


if __name__ == "__main__":
    recordings = main("/home/moose/Downloads/MfrDB_Symbols_v1.0")
