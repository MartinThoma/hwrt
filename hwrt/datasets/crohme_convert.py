#!/usr/bin/env python

"""Get all data in a CROHME folder as a feature vector list and a label
   list (Xs, ys) of single symbols. If it is a test folder, ys is None.
"""

# Core Library modules
import glob
import logging
import os
import pickle
import sys

# Third party modules
import click
import natsort
import numpy
import pkg_resources

# First party modules
from hwrt import classify
from hwrt.datasets import inkml
from hwrt.utils import less_than

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.DEBUG,
    stream=sys.stdout,
)


def main(folder):
    score_place = []
    wrong_counter = {}
    for hwr in read_folder(folder):
        results = classify.classify_segmented_recording(hwr.raw_data_json)
        score_place.append(get_position(results, hwr.formula_id))
        if score_place[-1] > 350:
            if hwr.formula_id not in wrong_counter:
                wrong_counter[hwr.formula_id] = 1
                logging.info("%i probably not in evaluation set?", hwr.formula_id)
            else:
                wrong_counter[hwr.formula_id] += 1

        if len(score_place) % 200 == 0:
            print("#" * 80)
            print_report(score_place)
    print("#" * 80)
    print_report(score_place)
    print("#" * 80)
    for key, value in sorted(
        list(wrong_counter.items()), reverse=True, key=lambda n: n[1]
    ):
        print(
            "http://www.martin-thoma.de/write-math/symbol/?id=%i :%i count"
            % (key, value)
        )


def read_folder(folder):
    """
    Parameters
    ----------
    folder : str

    Returns
    -------
    list of HandwrittenData objects
    """
    hwr_objects = []
    for filepath in natsort.natsorted(glob.glob("%s/*.inkml" % folder)):
        tmp = inkml.read(filepath)
        for hwr in tmp.to_single_symbol_list():
            hwr_objects.append(hwr)
    logging.info("Done reading formulas")
    save_raw_pickle(hwr_objects)
    return hwr_objects


def save_raw_pickle(hwr_objects):
    """
    Parameters
    ----------
    hwr_objects : list of hwr objects
    """
    converted_hwr = []

    translate = {}
    translate_id = {}
    model_path = pkg_resources.resource_filename("hwrt", "misc/")
    translation_csv = os.path.join(model_path, "latex2writemathindex.csv")
    arguments = {"newline": "", "encoding": "utf8"}
    with open(translation_csv, "rt", **arguments) as csvfile:
        contents = csvfile.read()
    lines = contents.split("\n")
    for csvrow in lines:
        csvrow = csvrow.split(",")
        if len(csvrow) == 1:
            writemathid = csvrow[0]
            latex = ""
        else:
            writemathid, latex = int(csvrow[0]), csvrow[1:]
            latex = ",".join(latex)
        translate[latex] = writemathid
        translate_id[writemathid] = latex

    for hwr in hwr_objects:
        hwr.formula_in_latex = translate_id[hwr.formula_id]

    formula_id2latex = {}
    for el in hwr_objects:
        if el.formula_id not in formula_id2latex:
            formula_id2latex[el.formula_id] = el.formula_in_latex

    for hwr in hwr_objects:
        hwr.formula_in_latex = translate_id[hwr.formula_id]
        hwr.raw_data_id = 42
        converted_hwr.append(
            {
                "is_in_testset": 0,
                "formula_id": hwr.formula_id,
                "handwriting": hwr,
                "id": 42,
                "formula_in_latex": hwr.formula_in_latex,
            }
        )
    with open("crohme.pickle", "wb") as f:
        pickle.dump(
            {
                "formula_id2latex": formula_id2latex,
                "handwriting_datasets": converted_hwr,
            },
            f,
            protocol=pickle.HIGHEST_PROTOCOL,
        )


def print_report(score_place):
    logging.info("Total: %i", len(score_place))
    logging.info("mean: %0.2f", numpy.mean(score_place))
    logging.info("median: %0.2f", numpy.median(score_place))
    for i in [1, 3, 10, 50]:
        logging.info(
            "TOP-%i error: %0.4f",
            i,
            (len(score_place) - less_than(score_place, i)) / len(score_place),
        )


def get_position(results, correct, default=10000):
    results = [int(el["semantics"].split(";")[0]) for el in results]
    if correct in results:
        return results.index(correct)
    else:
        return default


@click.command()
@click.option(
    "-f",
    "--folder",
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    help="read data from FOLDER",
    required=True,
)
def entry_point(folder):
    main(folder)


if __name__ == "__main__":
    entry_point()
