#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Start a webserver which can record the data and work as a classifier."""

import pkg_resources
from flask import Flask, request, render_template
from flask_bootstrap import Bootstrap

# hwrt modules
import hwrt.utils as utils


def show_results(results, n=10):
    """Show the TOP n results of a classification."""
    classification = ""
    classification += "{0:18s} {1:5s}\n".format("LaTeX Code", "Prob")
    classification += "#"*50 + "\n"
    for latex, probability in results:
        if n == 0:
            break
        else:
            n -= 1
        classification += "{0:18s} {1:5f}\n".format(latex, probability)
    classification += "#"*50 + "\n"
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
        json = request.form['drawnJSON']
        # TODO: Check recording
        # TODO: Submit recorded json to database
        # Classify
        results = utils.classify_single_recording(json,
                                                  model_folder="/home/moose/GitHub/hwr-experiments/models/baseline-2-c2",
                                                  verbose=False)
        # Show classification page
        return show_results(results, n=10) + '<a href="../interactive">back</a>'
    else:
        # Page where the user can enter a recording
        return render_template('canvas.html')


if __name__ == '__main__':
    app.run()
