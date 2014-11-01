#!/usr/bin/env python

import logging
import sys
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s",
                    level=logging.DEBUG,
                    stream=sys.stdout)
import time
import json

# GUI
import Tkinter as tk

# hwrt modules
import hwrt.utils as utils

recording = []
last_stroke = []
canvas = None


def unix_time():
    return int(round(time.time() * 1000))


def start(event):
    global recording
    recording.append([])


def motion(event):
    global recording, w
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
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-m", "--model",
                        dest="model",
                        help="where is the model folder (with a info.yml)?",
                        metavar="FOLDER",
                        type=lambda x: utils.is_valid_folder(parser, x),
                        default=utils.default_model())
    parser.add_argument("-v", "--verbose",
                        dest="verbose",
                        help="show recording before and after preprocessing",
                        action='store_true',
                        default=False)
    parser.add_argument("-n",
                        dest="n", default=10, type=int,
                        help="Show TOP-N results")
    return parser


def show_results(results, n=10):  # args.n
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


def main(model, n):
    global canvas
    root = tk.Tk()
    canvas = tk.Canvas(root, width=250, height=250)
    canvas.pack()
    root.bind('<B1-Motion>', motion)
    root.bind('<Button-1>', start)
    root.mainloop()
    raw_data_json = json.dumps(recording)
    logging.info(recording)
    logging.info("Start evaluation...")
    # TODO: use args.verbose instead of True if possible
    # args.model,
    results = utils.classify_single_recording(raw_data_json,
                                              model,
                                              True)
    show_results(results, n)


if __name__ == '__main__':
    args = get_parser().parse_args()
    main(args.model, args.n)
