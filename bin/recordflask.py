#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Start a webserver which can record the data and work as a classifier."""

import pkg_resources
from flask import Flask, request, render_template

# configuration
DEBUG = True

template_path = pkg_resources.resource_filename('hwrt', 'templates/')

# create our little application :)
app = Flask(__name__, template_folder=template_path)
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
        # TODO: Submit recorded json
        # TODO: Classify
        # TODO: Show classification page
        return json
    else:
        # Page where the user can enter a recording
        return render_template('canvas.html')


if __name__ == '__main__':
    app.run()
