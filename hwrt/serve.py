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

# Python 2 / 3 compatibility
from six.moves.urllib.request import urlopen
if sys.version_info[0] == 2:
    from future.builtins import open  # pylint: disable=W0622

# hwrt modules
import hwrt
import hwrt.utils as utils
import hwrt.classify as classify


# Global variables
n = 10


def submit_recording(raw_data_json):
    """Submit a recording to the database on write-math.com.

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
        raw_data_json = request.form['drawnJSON']

        # Check recording
        try:
            json.loads(raw_data_json)
        except ValueError:
            return "Invalid JSON string: %s" % raw_data_json

        # Submit recorded json to database
        try:
            submit_recording(raw_data_json)
        except requests.exceptions.ConnectionError:
            return ("Failed to submit this recording to write-math.com. "
                    "No internet connection?")

        # Classify
        results = classify.classify_segmented_recording(raw_data_json)

        # Show classification page
        page = show_results(results, n=n)
        page += '<a href="../interactive">back</a>'
        return page
    else:
        # Page where the user can enter a recording
        return render_template('canvas.html')


def get_json_result(results, n=10):
    """Return the top `n` results as a JSON list.
    >>> results = [{'symbolnr': 2,
    ...             'probability': 0.65,
    ...             'semantics': '\\alpha'},
    ...            {'symbolnr': 45,
    ...             'probability': 0.25,
    ...             'semantics': '\\propto'},
    ...            {'symbolnr': 15,
    ...             'probability': 0.0512,
    ...             'semantics': '\\varpropto'}]
    >>> get_json_result(results, n=10)
    [{'\\alpha': 0.65}, {'\\propto': 0.25}, {'\\varpropto': 0.0512}]
    """
    s = []
    for res in results[:min(len(results), n)]:
        s.append({res['semantics']: res['probability']})
    return json.dumps(s)


@app.route('/worker', methods=['POST', 'GET'])
def worker():
    """Implement a worker for write-math.com."""
    global n
    if request.method == 'POST':
        raw_data_json = request.form['classify']

        # Check recording
        try:
            json.loads(raw_data_json)
        except ValueError:
            return "Invalid JSON string: %s" % raw_data_json

        # Classify
        results = classify.classify_segmented_recording(raw_data_json)
        return get_json_result(results, n=n)
    else:
        # Page where the user can enter a recording
        return "Classification Worker (Version %s)" % hwrt.__version__


def fix_writemath_answer(results):
    """Bring ``results`` into a format that is accepted by write-math.com.
       This means using the ID for the formula that is used by the write-math
       server.

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

    for i, el in enumerate(results):
        semantics = el['semantics'].split(";")[1]
        if semantics not in translate:
            logging.debug("Could not find '%s' in translate.", semantics)
            logging.debug("el: %s", el)
            continue
        else:
            writemathid = translate[semantics]
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

    chunk_size = 1000

    logging.info("Start working!")
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

        print("http://www.martin-thoma.de/write-math/view/?raw_data_id=%s" %
              str(parsed_json['id']))

        # Classify
        results = classify.classify_segmented_recording(raw_data_json)

        # Submit classification to write-math server
        results = fix_writemath_answer(results)
        results_json = get_json_result(results, n=n)
        headers = {'User-Agent': 'Mozilla/5.0',
                   'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {'recording_id': parsed_json['id'],
                   'results': results_json,
                   'api_key': cmd['worker_api_key']}

        s = requests.Session()
        req = requests.Request('POST', url, headers=headers, data=payload)
        prepared = req.prepare()
        s.send(prepared)  # Returns: t.text = What was classified
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
    return parser


def main(port=8000, n_output=10):
    """Main function starting the webserver."""
    global n
    n = n_output
    logging.info("Start webserver...")
    app.run(port=port)

if __name__ == '__main__':
    global n
    args = get_parser().parse_args()
    n = args.n
    main(args.port)
