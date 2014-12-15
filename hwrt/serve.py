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
import csv

# Python 2 / 3 compatibility
from six.moves.urllib.request import urlopen
if sys.version_info[0] == 2:
    from future.builtins import open  # pylint: disable=W0622

# hwrt modules
import hwrt
import hwrt.utils as utils


# Global variables
preprocessing_queue = None
feature_list = None
model = None
output_semantics = None
n = 10


def submit_recording(raw_data_json):
    """Submit a recording to the database on write-math.com.

    :raises requests.exceptions.ConnectionError: if the internet connection is
    lost
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
    return '<a href="interactive">interactive</a>'


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
        model_path = pkg_resources.resource_filename('hwrt', 'misc/')
        model = os.path.join(model_path, "model.tar")
        logging.info("Model: %s", model)
        results = utils.evaluate_model_single_recording(model, raw_data_json)

        # Show classification page
        page = show_results(results, n=n)
        page += '<a href="../interactive">back</a>'
        return page
    else:
        # Page where the user can enter a recording
        return render_template('canvas.html')


def get_json_result(results, n=10):
    """Return the top ``n`` results as a json list.
    >>> results = [{'symbolnr': 2, \
                    'probability': 0.65, \
                    'semantics': '\\alpha'}, \
                   {'symbolnr': 45, \
                    'probability': 0.25, \
                    'semantics': '\\propto'}, \
                   {'symbolnr': 15, \
                    'probability': 0.0512, \
                    'semantics': '\\varpropto'}]
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
    global preprocessing_queue, feature_list, model, output_semantics, n
    if request.method == 'POST':
        raw_data_json = request.form['classify']

        # Check recording
        try:
            json.loads(raw_data_json)
        except ValueError:
            return "Invalid JSON string: %s" % raw_data_json

        # Classify
        evaluate = utils.evaluate_model_single_recording_preloaded
        results = evaluate(preprocessing_queue,
                           feature_list,
                           model,
                           output_semantics,
                           raw_data_json)
        return get_json_result(results, n=n)
    else:
        # Page where the user can enter a recording
        return "Classification Worker (Version %s)" % hwrt.__version__


def fix_writemath_answer(results):
    """Bring ``results`` into a format that is accepted by write-math.com.
       This means using the ID for the formula that is used by the write-math
       server.

    >>> results = [{'symbolnr': 214,
                    'semantics': '\\triangleq',
                    'probability': 0.03}, ...]
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
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for csvrow in spamreader:
            if len(csvrow) == 1:
                writemathid = csvrow[0]
                latex = ""
            else:
                writemathid, latex = csvrow
            translate[latex] = writemathid

    for i, el in enumerate(results):
        new_results.append({'symbolnr': el['symbolnr'],
                            'semantics': translate[el['semantics']],
                            'probability': el['probability']})
        if i >= 10 or (i > 0 and el['probability'] < 0.20):
            break
    return new_results


@app.route('/work', methods=['POST', 'GET'])
def work():
    """Implement a worker for write-math.com."""
    global preprocessing_queue, feature_list, model, output_semantics, n
    print("Start working!")
    for _ in range(1000):
        # contact the write-math server and get something to classify
        url = "http://www.martin-thoma.de/write-math/get_unclassified/"
        response = urlopen(url)
        page_source = response.read()
        parsed_json = json.loads(page_source)
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
        evaluate = utils.evaluate_model_single_recording_preloaded
        results = evaluate(preprocessing_queue,
                           feature_list,
                           model,
                           output_semantics,
                           raw_data_json)

        # Submit classification to write-math server
        results = fix_writemath_answer(results)
        results_json = get_json_result(results, n=n)
        headers = {'User-Agent': 'Mozilla/5.0',
                   'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {'recording_id': parsed_json['id'],
                   'results': results_json}

        s = requests.Session()
        req = requests.Request('POST', url, headers=headers, data=payload)
        prepared = req.prepare()
        s.send(prepared)
    return "Done"


def get_parser():
    """Return the parser object for this script."""
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-n",
                        dest="n", default=10, type=int,
                        help="Show TOP-N results")
    return parser


def main():
    """Main function starting the webserver."""
    global preprocessing_queue, feature_list, model, output_semantics, n
    logging.info("Start reading model...")
    model_path = pkg_resources.resource_filename('hwrt', 'misc/')
    model_file = os.path.join(model_path, "model.tar")
    (preprocessing_queue, feature_list, model,
     output_semantics) = utils.load_model(model_file)
    logging.info("Start webserver...")
    app.run()

if __name__ == '__main__':
    n = get_parser().parse_args().n
    main()
