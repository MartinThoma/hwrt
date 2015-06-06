#!/usr/bin/env python

"""Read and parse data from the MathBrush project."""

import os
from natsort import natsorted
import glob
import json
import re

import logging
import sys

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)

# hwrt modules
from hwrt import HandwrittenData
from hwrt import datasets

missing_stroke_segmentation = []
double_segmentation = []


def mathbrush_formula_fix(latex):
    fixit = [('lparen', '('),
             ('rparen', ')'),
             ('lbracket', '['),
             ('rbracket', ']'),
             ('eq', '='),
             ('gt', '>'),
             ('lt', '<'),
             ('plus', '+'),
             ('Integral', '\\int'),
             ('sqrt', '\\sqrt{}'),
             ('infin', '\\infty')]
    for search, replace in fixit:
        if latex == search:
            return replace
    return latex


def remove_matching_braces(latex):
    """
    If `latex` is surrounded by matching braces, remove them. They are not
    necessary.

    Parameters
    ----------
    latex : string

    Returns
    -------
    string

    Examples
    --------
    >>> remove_matching_braces('{2+2}')
    '2+2'
    >>> remove_matching_braces('{2+2')
    '{2+2'
    """
    if latex.startswith('{') and latex.endswith('}'):
        opened = 1
        matches = True
        for char in latex[1:-1]:
            if char == '{':
                opened += 1
            elif char == '}':
                opened -= 1
            if opened == 0:
                matches = False
        if matches:
            latex = latex[1:-1]
    return latex


def get_latex(ink_filename):
    """Get the LaTeX string from a file by the *.ink filename."""
    tex_file = os.path.splitext(ink_filename)[0] + ".tex"
    with open(tex_file) as f:
        tex_content = f.read().strip()
    pattern = re.compile(r"\\begin\{displaymath\}(.*?)\\end\{displaymath\}",
                         re.DOTALL)
    matches = pattern.findall(tex_content)

    if len(matches) == 0:
        pattern = re.compile(r"$$(.*?)$$",
                             re.DOTALL)
        matches = pattern.findall(tex_content)

    if len(matches) != 1:
        raise Exception("%s: Found not one match, but %i: %s" %
                        (ink_filename, len(matches), matches))
    formula_in_latex = matches[0].strip()
    formula_in_latex = remove_matching_braces(formula_in_latex)

    # repl = []
    # for letter in string.letters:
    #     repl.append(('\mbox{%s}' % letter, letter))
    # for search, replace in repl:
    #     formula_in_latex = formula_in_latex.replace(search, replace)
    return formula_in_latex


def get_segmentation(recording, annotations, internal_id=None):
    """
    Parameters
    ----------
    recording :
        A HandwrittenData object
    annotations : list of strings
    internal_id : string
        An identifier for the dataset, e.g. 'user1/200922-947-111.ink'.

    Returns
    -------
    tuple : segmentation and list of symbol ids (of write-math.com)
    """
    global missing_stroke_segmentation, double_segmentation
    segmentation = []
    symbol_stream = []
    needed = list(range(len(recording)))
    annotations = filter(lambda n: n.startswith('SYMBOL '), annotations)
    for line in annotations:
        tmp = line.split("<")[1]
        tmp, symbol_string = tmp.split(">")
        symbol_string = symbol_string.strip()
        strokes = [int(stroke) for stroke in tmp.split(",")
                   if int(stroke) < len(recording)]
        for el in strokes:
            if el not in needed:
                double_segmentation.append(internal_id)
                strokes.remove(el)
                logging.debug("invalid segmentation by annotation: %s",
                              annotations)
            else:
                needed.remove(el)
        segmentation.append(strokes)
        symbol_stream.append(datasets.formula_to_dbid(mathbrush_formula_fix(symbol_string), True))

    if len(needed) > 0:
        # hw = HandwrittenData.HandwrittenData(json.dumps(recording))
        # hw.show()
        missing_stroke_segmentation.append(internal_id)
        segmentation.append(needed)
    return segmentation, symbol_stream


def parse_scg_ink_file(filename):
    """Parse a SCG INK file.

    Parameters
    ----------
    filename : string
        The path to a SCG INK file.

    Returns
    -------
    HandwrittenData
        The recording as a HandwrittenData object.
    """
    stroke_count = 0
    stroke_point_count = -1
    recording = []
    current_stroke = []
    time = 0
    got_annotations = False
    annotations = []

    formula_in_latex = get_latex(filename)

    with open(filename) as f:
        contents = f.read().strip()
    lines = contents.split("\n")
    for i, line in enumerate(lines):
        line = line.strip()
        if i == 0 and line != 'SCG_INK':
            raise ValueError(("%s: SCG Ink files have to start with 'SCG_INK'."
                              " The file started with %s.") %
                             (filename, line))
        elif i == 1:
            try:
                stroke_count = int(line)
            except ValueError:
                raise ValueError(("%s: Second line has to be the number of "
                                  "strokeswhich has to be an integer, but "
                                  "was '%s'") % (filename, line))
            if stroke_count <= 0:
                # os.remove(filename)
                # return []
                raise ValueError(("%s: Stroke count was %i, but should be "
                                  "> 0.") % (filename, stroke_count))
        elif i == 2:
            try:
                stroke_point_count = int(line)
            except ValueError:
                raise ValueError("%s: Third line has to be the number of "
                                 "points which has to be an integer, but was "
                                 "'%s'" % (filename, line))
            if stroke_point_count <= 0:
                raise ValueError(("%s: Stroke point count was %i, but should "
                                  "be > 0.") % (filename, stroke_count))
        elif i > 2:
            if stroke_point_count > 0:
                x, y = [int(el) for el in line.strip().split(" ")]
                current_stroke.append({'x': x, 'y': y, 'time': time})
                time += 20
                stroke_point_count -= 1
            elif line == 'ANNOTATIONS' or got_annotations:
                got_annotations = True
                annotations.append(line)
            elif stroke_count > 0:
                try:
                    stroke_point_count = int(line)
                except ValueError:
                    raise ValueError(("%s: Line %i has to be the number of "
                                      "points which has to be an integer, "
                                      " but was '%s'") % (filename, i+1, line))
                if stroke_point_count <= 0:
                    raise ValueError(("%s: Stroke point count was %i, but "
                                      "should be > 0.") %
                                     (filename, stroke_count))
            if stroke_point_count == 0 and len(current_stroke) > 0:
                time += 200
                recording.append(current_stroke)
                stroke_count -= 1
                current_stroke = []
    hw = HandwrittenData.HandwrittenData(json.dumps(recording),
                                         formula_in_latex=formula_in_latex,
                                         formula_id=datasets.formula_to_dbid(mathbrush_formula_fix(formula_in_latex)))
    hw.internal_id = "/".join(filename.split("/")[-2:])
    hw.segmentation, hw.symbol_stream = get_segmentation(recording,
                                                         annotations,
                                                         hw.internal_id)
    hw.description = "\n".join(annotations)
    hw.username = "MathBrush::%s" % os.path.basename(os.path.dirname(filename))
    copyright_str = ("This dataset was contributed by MathBrush. You can "
                     "download their complete dataset by contacting them. See "
                     "[www.scg.uwaterloo.ca/mathbrush/]"
                     "(https://www.scg.uwaterloo.ca/mathbrush/publications/corpus.pdf)")
    hw.user_id = datasets.getuserid(hw.username, copyright_str)
    return hw


def read_folder(folder):
    """Read all files of `folder` and return a list of HandwrittenData
    objects.

    Parameters
    ----------
    folder : string
        Path to a folder

    Returns
    -------
    list :
        A list of all .ink files in the given folder.
    """
    recordings = []
    for filename in glob.glob(os.path.join(folder, '*.ink')):
        recording = parse_scg_ink_file(filename)
        recordings.append(recording)
    return recordings


def main(directory):
    user_dirs = natsorted(list(next(os.walk(directory))[1]))
    recordings = []
    for user_dir in user_dirs:
        user_dir = os.path.join(directory, user_dir)
        logging.info("Start getting data from %s...", user_dir)
        recordings += read_folder(user_dir)
    logging.info("Got %i recordings.", len(recordings))
    logging.info("Double segmented strokes: %i (%0.2f%%)",
                 len(double_segmentation),
                 float(len(double_segmentation))/len(recordings))
    logging.info("Missing segmented strokes: %i (%0.2f%%)",
                 len(missing_stroke_segmentation),
                 float(len(missing_stroke_segmentation))/len(recordings))
    for recording in recordings:
        datasets.insert_recording(recording)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    main("/home/moose/Downloads/mathbrush/mathdata")
