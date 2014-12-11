#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pkg_resources

# hwrt modules
import hwrt.record as record


# Test helpers
class Object(object):
    pass


def create_line(s, width=3, fill="red", smooth=True):
    return True


# Tests
def execution_test():
    record.unix_time()
    record.start(0)

    record.recording = [[{'x': 0, 'y': 0}]]
    evt = Object()
    evt.x = 12
    evt.y = 13
    record.canvas = Object()
    record.canvas.create_line = create_line
    record.motion(evt)

    record.get_parser()


def results_test():
    results = [("\\alpha", 0.5), ("\\beta", 0.4)]
    record.show_results(results, n=10)

    results = [("a", 0.5), ("b", 0.4), ("c", 0.1), ("d", 0.1), ("e", 0.1),
               ("f", 0.1), ("g", 0.1), ("h", 0.1), ("i", 0.1), ("j", 0.1),
               ("k", 0.1), ("l", 0.1), ("m", 0.1), ("n", 0.1), ("o", 0.1)]
    record.show_results(results, n=10)
