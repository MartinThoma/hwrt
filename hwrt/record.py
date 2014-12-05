#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Record new handwritten symbol and classify it."""

import logging
import sys
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)
import time
import json
import pkg_resources
import os

# GUI
try:
    # for Python2
    import Tkinter as tk
except ImportError:
    # for Python3
    import tkinter as tk

# hwrt modules
import hwrt.utils as utils

recording = []
last_stroke = []
canvas = None


def unix_time():
    """Get current UNIX time in milliseconds (since 1970)."""
    return int(round(time.time() * 1000))


def start(_):
    """Start a new stroke."""
    global recording
    recording.append([])


def motion(event):
    """Record points of a stroke."""
    global recording, canvas
    if len(recording) > 0:
        x, y = event.x, event.y
        recording[-1].append({'x': x, 'y': y, 'time': unix_time()})
        if len(recording[-1]) >= 2:
            #canvas.get_tk_widget().delete("all")
            for stroke in recording:
                s = [(p['x'], p['y']) for p in stroke]
                canvas.create_line(s,
                                   width=3, fill="red",
                                   smooth=True)


def get_parser():
    """Get parser object for record.py"""
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    model_path = pkg_resources.resource_filename('hwrt', 'misc/')
    model_file = os.path.join(model_path, "model.tar")
    parser.add_argument("-m", "--model",
                        dest="model",
                        help="where is the model file (.tar)?",
                        metavar="FILE",
                        type=lambda x: utils.is_valid_file(parser, x),
                        default=model_file)
    parser.add_argument("-v", "--verbose",
                        dest="verbose",
                        help="show recording before and after preprocessing",
                        action='store_true',
                        default=False)
    parser.add_argument("-n",
                        dest="n", default=10, type=int,
                        help="Show TOP-N results")
    return parser


def show_results(results, n=10):
    """Show the TOP n results of a classification."""
    # Print headline
    print("{0:18s} {1:5s}".format("LaTeX Code", "Prob"))
    print("#"*50)
    for latex, probability in results:
        if n == 0:
            break
        else:
            n -= 1
        print("{0:18s} {1:5f}".format(latex, probability))
    print("#"*50)


def main(model, n, verbose):
    """Main of record.py"""
    global canvas
    root = tk.Tk()
    canvas = tk.Canvas(root, width=250, height=250)
    canvas.pack()
    root.bind('<B1-Motion>', motion)
    root.bind('<Button-1>', start)
    root.mainloop()
    raw_data_json = json.dumps(recording)
    results = utils.evaluate_model_single_recording(model, raw_data_json)
    import nntoolkit
    nntoolkit.evaluate.show_results(results, n)


if __name__ == '__main__':
    args = get_parser().parse_args()
    main(args.model, args.n, args.verbose)
