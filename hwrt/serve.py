#!/usr/bin/env python

"""Start a webserver which can record the data and work as a classifier."""

# Core Library modules
import json
import logging
import os
import uuid
from typing import Any, Dict, List, Optional

# Third party modules
import pkg_resources
import requests
from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from six.moves.urllib.request import urlopen

# First party modules
import hwrt

# Local modules
from . import classify
from . import segmentation as se
from . import utils

logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)


# Global variables
n = 10
use_segmenter_flag = False


def submit_recording(raw_data_json):
    """Submit a recording to the database on write-math.com.

    Parameters
    ----------
    raw_data_json : str
        Raw data in JSON format

    Raises
    ------
    requests.exceptions.ConnectionError
        If the internet connection is lost.
    """
    url = "http://www.martin-thoma.de/write-math/classify/index.php"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {"drawnJSON": raw_data_json}

    s = requests.Session()
    req = requests.Request("POST", url, headers=headers, data=payload)
    prepared = req.prepare()
    s.send(prepared)


def show_results(results: List[Dict[str, float]], n: int = 10) -> str:
    r"""Show the TOP n results of a classification.
    >>> results = [{'\\alpha': 0.67, 'semantics': '\\alpha', 'probability': 0.67},
    ... {'\\propto': 0.25, 'semantics': '\\propto', 'probability': 0.33}]
    >>> result_str = show_results(results)
    Class              Prob
    ##################################################
    \alpha             67.0000%
    \propto            33.0000%
    ##################################################

    """
    import nntoolkit.evaluate

    classification = nntoolkit.evaluate.show_results(results, n)
    return "<pre>" + classification.replace("\n", "<br/>") + "</pre>"


# configuration
DEBUG = True

template_path = utils.get_template_folder()

app = Flask(__name__, template_folder=template_path)
Bootstrap(app)
app.config.from_object(__name__)


@app.route("/", methods=["GET"])
def interactive():
    """Interactive classifier."""
    if request.method == "GET" and request.args.get("heartbeat", "") != "":
        return request.args.get("heartbeat", "")
    return render_template("canvas.html")


def get_json_result(results: List[Dict[str, Any]], n: int = 10) -> str:
    """Return the top `n` results as a JSON list.

    Examples
    --------
    >>> results = [{'probability': 0.65,
    ...             'whatever': 'bar'},
    ...            {'probability': 0.21,
    ...             'whatever': 'bar'},
    ...            {'probability': 0.05,
    ...             'whatever': 'bar'},]
    >>> get_json_result(results, n=2)
    '[{"probability": 0.65, "whatever": "bar"}, {"probability": 0.21, "whatever": "bar"}]'
    """
    s = []
    last = -1
    for res in results[: min(len(results), n)]:
        if res["probability"] < last * 0.5 and res["probability"] < 0.05:
            break
        if res["probability"] < 0.01:
            break
        s.append(res)
        last = res["probability"]
    return json.dumps(s)


@app.route("/worker", methods=["POST", "GET"])
def worker():
    """Implement a worker for write-math.com."""
    global n
    global use_segmenter_flag
    if request.method == "POST":
        raw_data_json = request.form["classify"]
        secret_uuid = request.form.get("secret", None)
        if secret_uuid is None:
            logger.info("No secret uuid given. Create one.")
            secret_uuid = str(uuid.uuid4())

        # Check recording
        try:
            json.loads(raw_data_json)
        except ValueError:
            return "Invalid JSON string: %s" % raw_data_json

        # Classify
        if use_segmenter_flag:
            strokelist = json.loads(raw_data_json)
            beam = utils.get_beam(secret_uuid)

            if beam is None:
                beam = se.Beam()
                for stroke in strokelist:
                    beam.add_stroke(stroke)
                results = beam.get_results()
                utils.store_beam(beam, secret_uuid)
            else:
                stroke = strokelist[-1]
                beam.add_stroke(stroke)
                results = beam.get_results()
                utils.store_beam(beam, secret_uuid)
        else:
            results = classify.classify_segmented_recording(raw_data_json)
        return get_json_result(results, n=n)
    else:
        # Page where the user can enter a recording
        return "Classification Worker (Version %s)" % hwrt.__version__


def _get_part(pointlist, strokes):
    """Get some strokes of pointlist

    Parameters
    ----------
    pointlist : list of lists of dicts
    strokes : list of integers

    Returns
    -------
    list of lists of dicts
    """
    result = []
    strokes = sorted(strokes)
    for stroke_index in strokes:
        result.append(pointlist[stroke_index])
    return result


def _get_translate() -> Dict[str, str]:
    """
    Get a dictionary which translates from a neural network output to
    semantics.
    """
    translate = {}
    model_path = pkg_resources.resource_filename("hwrt", "misc/")
    translation_csv = os.path.join(model_path, "latex2writemathindex.csv")
    with open(translation_csv, newline="", encoding="utf8") as csvfile:
        contents = csvfile.read()
    lines = contents.split("\n")
    for csvrow_str in lines:
        csvrow = csvrow_str.split(",")
        if len(csvrow) == 1:
            writemathid = csvrow[0]
            latex = ""
        else:
            writemathid, latex_list = csvrow[0], csvrow[1:]
            latex = ",".join(latex_list)
        translate[latex] = writemathid
    return translate


def get_writemath_id(el: Dict[Any, Any], translate) -> Optional[int]:
    """
    Parameters
    ----------
    el : Dict
        with key 'semantics'
        results element

    Returns
    -------
    writemathid: Optional[int]
        ID of the symbol on write-math.com
    """
    semantics = el["semantics"].split(";")[1]
    if semantics not in translate:
        logger.debug(f"Could not find '{semantics}' in translate. el={el}")
        return None
    else:
        writemathid = translate[semantics]
    return writemathid


def fix_writemath_answer(results: List[Dict[str, Any]]):
    """
    Bring ``results`` into a format that is accepted by write-math.com. This
    means using the ID for the formula that is used by the write-math server.

    Examples
    --------
    >>> results = [{'symbolnr': 214,
    ...             'semantics': 'foobar;A',
    ...             'probability': 0.03}]
    >>> fix_writemath_answer(results)
    [{'symbolnr': 214, 'semantics': '31', 'probability': 0.03}]
    """
    new_results = []
    # Read csv
    translate = _get_translate()

    for i, el in enumerate(results):
        writemathid = get_writemath_id(el, translate)
        if writemathid is None:
            continue
        new_results.append(
            {
                "symbolnr": el["symbolnr"],
                "semantics": writemathid,
                "probability": el["probability"],
            }
        )
        if i >= 10 or (i > 0 and el["probability"] < 0.20):
            break
    return new_results


@app.route("/work", methods=["POST", "GET"])
def work():
    """Implement a worker for write-math.com."""
    global n

    cmd = utils.get_project_configuration()
    if "worker_api_key" not in cmd:
        return "You need to define a 'worker_api_key' in your ~/"

    chunk_size = 1000

    logger.info("Start working with n=%i", n)
    for _ in range(chunk_size):
        # contact the write-math server and get something to classify
        url = "http://www.martin-thoma.de/write-math/api/get_unclassified.php"
        response = urlopen(url)
        page_source = response.read()
        parsed_json = json.loads(page_source)
        if parsed_json is False:
            return "Nothing left to classify"
        raw_data_json = parsed_json["recording"]

        # Classify
        # Check recording
        try:
            json.loads(raw_data_json)
        except ValueError:
            return "Raw Data ID {}; Invalid JSON string: {}".format(
                parsed_json["id"], raw_data_json,
            )

        # Classify
        if use_segmenter_flag:
            strokelist = json.loads(raw_data_json)
            beam = se.Beam()
            for stroke in strokelist:
                beam.add_stroke(stroke)
            results = beam.get_writemath_results()
        else:
            results_sym = classify.classify_segmented_recording(raw_data_json)
            results = []
            strokelist = json.loads(raw_data_json)
            segmentation = [list(range(len(strokelist)))]
            translate = _get_translate()
            for symbol in results_sym:
                s = {
                    "id": get_writemath_id(symbol, translate),
                    "probability": symbol["probability"],
                }
                results.append(
                    {
                        "probability": symbol["probability"],
                        "segmentation": segmentation,
                        "symbols": [s],
                    }
                )

        print("\thttp://write-math.com/view/?raw_data_id=%s" % str(parsed_json["id"]))

        # Submit classification to write-math.com server
        results_json = get_json_result(results, n=n)
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {
            "recording_id": parsed_json["id"],
            "results": results_json,
            "api_key": cmd["worker_api_key"],
        }

        s = requests.Session()
        req = requests.Request("POST", url, headers=headers, data=payload)
        prepared = req.prepare()
        response = s.send(prepared)
        try:
            response = json.loads(response.text)
        except ValueError:
            return "Invalid JSON response: %s" % response.text

        if "error" in response:
            logger.info(response)
            return str(response)
    return "Done - Classified %i recordings" % chunk_size


def main(port=8000, n_output=10, use_segmenter=False):
    """Main function starting the webserver."""
    global n
    global use_segmenter_flag
    n = n_output
    use_segmenter_flag = use_segmenter
    logger.info("Start webserver...")
    app.run(port=port)
