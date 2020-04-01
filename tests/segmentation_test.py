#!/usr/bin/env python

"""Tests for the segmentation subpackage."""

# First party modules
import hwrt.segmentation as segmentation
import tests.testhelper as testhelper


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


def test_get_results():
    """Test the .get_results() method of beam objects."""
    beams = prepare_beams()
    for beam in beams:
        beam.get_results()


def test_get_writemath_results():
    """Test the .get_writemath_results method of beam objects."""
    beams = prepare_beams()
    for beam in beams:
        beam.get_writemath_results()
