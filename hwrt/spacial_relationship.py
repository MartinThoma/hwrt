#!/usr/bin/env python

"""
Functions to estimate the spacial relationship of
two symbols.
"""


def estimate(s1, s2):
    """
    Estimate the spacial relationship by
    examining the position of the bounding boxes.

    Parameters
    ----------
    s1 : HandwrittenData
    s2 : HandwrittenData

    Returns
    -------
    dict of probabilities
        {'bottom': 0.1,
         'subscript': 0.2,
         'right': 0.3,
         'superscript': 0.3,
         'top': 0.1}
    """
    s1bb = s1.get_bounding_box()
    s2bb = s2.get_bounding_box()
    total_area = (s2bb["maxx"] - s2bb["minx"] + 1) * (s2bb["maxy"] - s2bb["miny"] + 1)
    total_area = float(total_area)
    top_area = 0.0
    superscript_area = 0.0
    right_area = 0.0
    subscript_area = 0.0
    bottom_area = 0.0
    # bottom
    if s2bb["maxy"] > s1bb["maxy"] and s2bb["minx"] < s1bb["maxx"]:
        miny = max(s2bb["miny"], s1bb["maxy"])
        maxy = s2bb["maxy"]
        minx = max(s2bb["minx"], s1bb["minx"])
        maxx = min(s2bb["maxx"], s1bb["maxx"])
        bottom_area = float((maxx - minx) * (maxy - miny))
    # Subscript
    if s2bb["maxy"] > s1bb["maxy"] and s2bb["maxx"] > s1bb["maxx"]:
        miny = max(s2bb["miny"], s1bb["maxy"])
        maxy = s2bb["maxy"]
        minx = max(s2bb["minx"], s1bb["maxx"])
        maxx = s2bb["maxx"]
        subscript_area = (maxx - minx) * (maxy - miny)
    # right
    if (
        s2bb["miny"] < s1bb["maxy"]
        and s2bb["maxy"] > s1bb["miny"]
        and s2bb["maxx"] > s1bb["maxx"]
    ):
        miny = max(s1bb["miny"], s2bb["miny"])
        maxy = min(s1bb["maxy"], s2bb["maxy"])
        minx = max(s1bb["maxx"], s2bb["minx"])
        maxx = s2bb["maxx"]
        right_area = (maxx - minx) * (maxy - miny)
    # superscript
    if s2bb["miny"] < s1bb["miny"] and s2bb["maxx"] > s1bb["maxx"]:
        miny = s2bb["miny"]
        maxy = min(s1bb["miny"], s2bb["maxy"])
        minx = max(s1bb["maxx"], s2bb["minx"])
        maxx = s2bb["maxx"]
        superscript_area = (maxx - minx) * (maxy - miny)
    # top
    if s2bb["miny"] < s1bb["miny"] and s2bb["minx"] < s1bb["maxx"]:
        miny = s2bb["miny"]
        maxy = min(s1bb["miny"], s2bb["maxy"])
        minx = max(s1bb["minx"], s2bb["minx"])
        maxx = min(s1bb["maxx"], s2bb["maxx"])
        top_area = (maxx - minx) * (maxy - miny)

    return {
        "bottom": bottom_area / total_area,
        "subscript": subscript_area / total_area,
        "right": right_area / total_area,
        "superscript": superscript_area / total_area,
        "top": top_area / total_area,
    }
