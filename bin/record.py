#!/usr/bin/env python

import logging
import sys
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s",
                    level=logging.DEBUG,
                    stream=sys.stdout)
import time
import json
# GUI
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line
from kivy.logger import Logger
Logger.setLevel(logging.ERROR)
# mine
import hwrt.utils as utils


def unix_time():
    return int(round(time.time() * 1000))


recording = []
last_stroke = []


class MyPaintWidget(Widget):

    def on_touch_down(self, touch):
        global recording, last_stroke
        with self.canvas:
            Color(1, 1, 0)
            d = 5.
            Ellipse(pos=(touch.x - d / 2, touch.y - d / 2), size=(d, d))
            touch.ud['line'] = Line(points=(touch.x, touch.y))
            # Record keeping
            if len(last_stroke) > 0:
                recording.append(last_stroke)
                last_stroke = []
            point = {"x": touch.x, "y": -touch.y, "time": unix_time()}
            last_stroke.append(point)

    def on_touch_move(self, touch):
        global last_stroke
        touch.ud['line'].points += [touch.x, touch.y]
        # Record keeping
        point = {"x": touch.x, "y": -touch.y, "time": unix_time()}
        last_stroke.append(point)


class MyPaintApp(App):

    def build(self):
        return MyPaintWidget()


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


if __name__ == '__main__':
    args = get_parser().parse_args()
    MyPaintApp().run()
    recording.append(last_stroke)
    last_stroke = []
    raw_data_json = json.dumps(recording)
    logging.info(recording)
    logging.info("Start evaluation...")
    # TODO: use args.verbose instead of True if possible
    results = utils.classify_single_recording(raw_data_json,
                                              args.model,
                                              True)
    n = args.n

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
