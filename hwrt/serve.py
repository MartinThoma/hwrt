#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Start a webserver which can record the data and work as a classifier."""

import pkg_resources
from flask import Flask, request, render_template
from flask_bootstrap import Bootstrap
import os
import json

# hwrt modules
import hwrt
import hwrt.utils as utils


def show_results(results, n=10):
    """Show the TOP n results of a classification."""
    import nntoolkit
    classification = nntoolkit.evaluate.show_results(results, n)
    return "<pre>" + classification.replace("\n", "<br/>") + "</pre>"

# configuration
DEBUG = True

template_path = pkg_resources.resource_filename('hwrt', 'templates/')
template_path = "/home/moose/GitHub/hwrt/hwrt/templates/"

# create our little application :)
app = Flask(__name__, template_folder=template_path)
Bootstrap(app)
app.config.from_object(__name__)


@app.route('/', methods=['POST', 'GET'])
def show_entries():
    heartbeat = request.args.get('heartbeat', '')
    return heartbeat


@app.route('/interactive', methods=['POST', 'GET'])
def interactive():
    if request.method == 'POST':
        raw_data_json = request.form['drawnJSON']
        # TODO: Check recording
        # TODO: Submit recorded json to database
        # Classify
        model_path = pkg_resources.resource_filename('hwrt', 'misc/')
        model = os.path.join(model_path, "model.tar")
        print(model)
        results = utils.evaluate_model_single_recording(model, raw_data_json)
        # Show classification page
        page = show_results(results, n=10)
        page += '<a href="../interactive">back</a>'
        return page
    else:
        # Page where the user can enter a recording
        return render_template('canvas.html')


def get_json_result(results, n=10):
    s = []
    for res in results[:min(len(results), n)]:
        s.append({res['semantics']: res['probability']})
    return json.dumps(s)


@app.route('/worker', methods=['POST', 'GET'])
def worker():
    # Test with
    # wget --post-data 'classify=%5B%5B%7B%22x%22%3A334%2C%22y%22%3A407%2C%22time%22%3A1417704378719%7D%5D%5D' http://127.0.0.1:5000/worker
    if request.method == 'POST':
        raw_data_json = request.form['classify']
        # TODO: Check recording
        # TODO: Submit recorded json to database
        # Classify
        model_path = pkg_resources.resource_filename('hwrt', 'misc/')
        model = os.path.join(model_path, "model.tar")
        results = utils.evaluate_model_single_recording(model, raw_data_json)
        return get_json_result(results, n=10)
    else:
        # Page where the user can enter a recording
        return "Classification Worker (Version %s)" % hwrt.__version__


def get_parser():
    """Return the parser object for this script."""
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    return parser


def main():
    app.run()

if __name__ == '__main__':
    main()
