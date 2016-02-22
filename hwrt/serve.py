#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Start a webserver which can record the data and work as a classifier."""

import pkg_resources
from flask import Flask, request, render_template
from flask_bootstrap import Bootstrap
import os
import sys
import json
import requests
import logging
import uuid

logging.getLogger("requests").setLevel(logging.WARNING)

# Python 2 / 3 compatibility
from six.moves.urllib.request import urlopen
if sys.version_info[0] == 2:
    from future.builtins import open  # pylint: disable=W0622

# hwrt modules
import hwrt
from . import utils
from . import classify
from . import segmentation as se

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
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {'drawnJSON': raw_data_json}

    s = requests.Session()
    req = requests.Request('POST', url, headers=headers, data=payload)
    prepared = req.prepare()
    s.send(prepared)


def show_results(results, n=10):
    """Show the TOP n results of a classification.
    >>> results = [{'\\alpha': 0.67}, {'\\propto': 0.25}]
    >>> show_results(results)
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


@app.route('/', methods=['POST', 'GET'])
def index():
    """Start page."""
    return ('<a href="interactive">interactive</a> - '
            '<a href="work">Classify stuff on write-math.com</a>')


@app.route('/interactive', methods=['POST', 'GET'])
def interactive():
    """Interactive classifier."""
    global n
    if request.method == 'GET' and request.args.get('heartbeat', '') != "":
        return request.args.get('heartbeat', '')
    if request.method == 'POST':
        logging.warning('POST to /interactive is deprecated. '
                        'Use /worker instead')
    else:
        # Page where the user can enter a recording
        return render_template('canvas.html')


def get_json_result(results, n=10):
    """Return the top `n` results as a JSON list.
    >>> results = [{'probability': 0.65,
    ...             'whatever': 'bar'},
    ...            {'probability': 0.21,
    ...             'whatever': 'bar'},
    ...            {'probability': 0.05,
    ...             'whatever': 'bar'},]
    >>> get_json_result(results, n=10)
    [{'\\alpha': 0.65}, {'\\propto': 0.25}, {'\\varpropto': 0.0512}]
    """
    s = []
    last = -1
    for res in results[:min(len(results), n)]:
        if res['probability'] < last*0.5 and res['probability'] < 0.05:
            break
        if res['probability'] < 0.01:
            break
        s.append(res)
        last = res['probability']
    return json.dumps(s)


@app.route('/worker', methods=['POST', 'GET'])
def worker():
    """Implement a worker for write-math.com."""
    global n
    global use_segmenter_flag
    if request.method == 'POST':
        raw_data_json = request.form['classify']
        try:
            secret_uuid = request.form['secret']
        except:
            logging.info("No secret uuid given. Create one.")
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


def _get_translate():
    """
    Get a dictionary which translates from a neural network output to
    semantics.
    """
    translate = {}
    model_path = pkg_resources.resource_filename('hwrt', 'misc/')
    translation_csv = os.path.join(model_path, 'latex2writemathindex.csv')
    arguments = {'newline': '', 'encoding': 'utf8'}
    with open(translation_csv, 'rt', **arguments) as csvfile:
        contents = csvfile.read()
    lines = contents.split("\n")
    for csvrow in lines:
        csvrow = csvrow.split(',')
        if len(csvrow) == 1:
            writemathid = csvrow[0]
            latex = ""
        else:
            writemathid, latex = csvrow[0], csvrow[1:]
            latex = ','.join(latex)
        translate[latex] = writemathid
    return translate


def get_writemath_id(el, translate):
    """
    Parameters
    ----------
    el : dict
        with key 'semantics'
        results element

    Returns
    -------
    int or None:
        ID of the symbol on write-math.com
    """
    semantics = el['semantics'].split(";")[1]
    if semantics not in translate:
        logging.debug("Could not find '%s' in translate.", semantics)
        logging.debug("el: %s", el)
        return None
    else:
        writemathid = translate[semantics]
    return writemathid


def fix_writemath_answer(results):
    """
    Bring ``results`` into a format that is accepted by write-math.com. This
    means using the ID for the formula that is used by the write-math server.

    Examples
    --------
    >>> results = [{'symbolnr': 214,
    ...             'semantics': '\\triangleq',
    ...             'probability': 0.03}, ...]
    >>> fix_writemath_answer(results)
    [{123: 0.03}, ...]
    """
    new_results = []
    # Read csv
    translate = _get_translate()

    for i, el in enumerate(results):
        writemathid = get_writemath_id(el, translate)
        if writemathid is None:
            continue
        new_results.append({'symbolnr': el['symbolnr'],
                            'semantics': writemathid,
                            'probability': el['probability']})
        if i >= 10 or (i > 0 and el['probability'] < 0.20):
            break
    return new_results


@app.route('/work', methods=['POST', 'GET'])
def work():
    """Implement a worker for write-math.com."""
    global n

    cmd = utils.get_project_configuration()
    if 'worker_api_key' not in cmd:
        return ("You need to define a 'worker_api_key' in your ~/")

    chunk_size = 1000

    logging.info("Start working with n=%i", n)
    for _ in range(chunk_size):
        # contact the write-math server and get something to classify
        url = "http://www.martin-thoma.de/write-math/api/get_unclassified.php"
        response = urlopen(url)
        page_source = response.read()
        parsed_json = json.loads(page_source)
        if parsed_json is False:
            return "Nothing left to classify"
        raw_data_json = parsed_json['recording']

        # Classify
        # Check recording
        try:
            json.loads(raw_data_json)
        except ValueError:
            return ("Raw Data ID %s; Invalid JSON string: %s" %
                    (parsed_json['id'], raw_data_json))

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
                s = {'id': get_writemath_id(symbol, translate),
                     'probability': symbol['probability']}
                results.append({'probability': symbol['probability'],
                                'segmentation': segmentation,
                                'symbols': [s]})

        print("\thttp://write-math.com/view/?raw_data_id=%s" %
              str(parsed_json['id']))

        # Submit classification to write-math.com server
        results_json = get_json_result(results, n=n)
        headers = {'User-Agent': 'Mozilla/5.0',
                   'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {'recording_id': parsed_json['id'],
                   'results': results_json,
                   'api_key': cmd['worker_api_key']}

        s = requests.Session()
        req = requests.Request('POST', url, headers=headers, data=payload)
        prepared = req.prepare()
        response = s.send(prepared)
        try:
            response = json.loads(response.text)
        except ValueError:
            return "Invalid JSON response: %s" % response.text

        if 'error' in response:
            logging.info(response)
            return str(response)
    return "Done - Classified %i recordings" % chunk_size


def get_parser():
    """Return the parser object for this script."""
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-n",
                        dest="n", default=10, type=int,
                        help="Show TOP-N results")
    parser.add_argument("--port",
                        dest="port", default=5000, type=int,
                        help="where should the webserver run")
    parser.add_argument("--use_segmenter",
                        dest="use_segmenter",
                        default=False,
                        action='store_true',
                        help=("try to segment the input for multiple symbol "
                              "recognition"))
    return parser


def main(port=8000, n_output=10, use_segmenter=False):
    """Main function starting the webserver."""
    global n
    global use_segmenter_flag
    n = n_output
    use_segmenter_flag = use_segmenter
    logging.info("Start webserver...")
    app.run(port=port)

if __name__ == '__main__':
    global n
    args = get_parser().parse_args()
    n = args.n
    main(port=args.port, use_segmenter=args.use_segmenter)
