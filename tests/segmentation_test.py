#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the segmentation subpackage."""

# import nose
import tests.testhelper as testhelper

# hwrt modules
import hwrt.segmentation as segmentation
# import hwrt.utils as utils


# Tests
def prepare_beams():
    """
    Prepare one beam object for each recording.

    Returns
    -------
    list
        A list of beam objects
    """
    beams = []
    hwrs = testhelper.get_all_symbols_as_handwriting()
    for hwr in hwrs:
        beam = segmentation.Beam()
        for stroke in hwr.get_sorted_pointlist():
            beam.add_stroke(stroke)
        beams.append(beam)
    return beams


def get_results_test():
    """Test the .get_results() method of beam objects."""
    beams = prepare_beams()
    for beam in beams:
        beam.get_results()


def get_writemath_results_test():
    """Test the .get_writemath_results method of beam objects."""
    beams = prepare_beams()
    for beam in beams:
        beam.get_writemath_results()


# def p_strokes_test():
#     nose.tools.assert_greater_equal(1.0, segmentation.p_strokes('A', 3))
#     nose.tools.assert_greater_equal(segmentation.p_strokes('A', 3), 0.0)
