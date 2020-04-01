#!/usr/bin/env python

# Core Library modules
import json
import logging
import signal
import sys
from xml.dom.minidom import parseString

# Third party modules
from natsort import natsorted

# Local modules
from .. import handwritten_data
from ..datasets import formula_to_dbid

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.DEBUG,
    stream=sys.stdout,
)


def beautify_xml(path):
    """
    Beautify / pretty print XML in `path`.

    Parameters
    ----------
    path : str

    Returns
    -------
    str
    """
    with open(path) as f:
        content = f.read()

    def pretty_print(data):
        return "\n".join(
            [
                line
                for line in parseString(data).toprettyxml(indent=" " * 2).split("\n")
                if line.strip()
            ]
        )

    return pretty_print(content)


def normalize_symbol_name(symbol_name):
    """
    Change symbol names to a version which is known by write-math.com

    Parameters
    ----------
    symbol_name : str

    Returns
    -------
    str
    """
    if symbol_name == "\\frac":
        return "\\frac{}{}"
    elif symbol_name == "\\sqrt":
        return "\\sqrt{}"
    elif symbol_name in ["&lt;", r"\lt"]:
        return "<"
    elif symbol_name in ["&gt;", r"\gt"]:
        return ">"
    elif symbol_name == "{":
        return r"\{"
    elif symbol_name == "}":
        return r"\}"
    return symbol_name


def read(filepath):
    """
    Read a single InkML file

    Parameters
    ----------
    filepath : string
        path to the (readable) InkML file

    Returns
    -------
    HandwrittenData :
        The parsed InkML file as a HandwrittenData object
    """
    import xml.etree.ElementTree

    root = xml.etree.ElementTree.parse(filepath).getroot()

    # Get the raw data
    recording = []
    strokes = sorted(
        root.findall("{http://www.w3.org/2003/InkML}trace"),
        key=lambda child: int(child.attrib["id"]),
    )
    time = 0
    for stroke in strokes:
        stroke = stroke.text.strip().split(",")
        stroke = [point.strip().split(" ") for point in stroke]
        if len(stroke[0]) == 3:
            stroke = [
                {"x": float(x), "y": float(y), "time": float(t)} for x, y, t in stroke
            ]
        else:
            stroke = [{"x": float(x), "y": float(y)} for x, y in stroke]
            new_stroke = []
            for p in stroke:
                new_stroke.append({"x": p["x"], "y": p["y"], "time": time})
                time += 20
            stroke = new_stroke
            time += 200
        recording.append(stroke)

    # Get LaTeX
    formula_in_latex = None
    annotations = root.findall("{http://www.w3.org/2003/InkML}annotation")
    for annotation in annotations:
        if annotation.attrib["type"] == "truth":
            formula_in_latex = annotation.text
    hw = handwritten_data.HandwrittenData(
        json.dumps(recording), formula_in_latex=formula_in_latex
    )
    for annotation in annotations:
        if annotation.attrib["type"] == "writer":
            hw.writer = annotation.text
        elif annotation.attrib["type"] == "category":
            hw.category = annotation.text
        elif annotation.attrib["type"] == "expression":
            hw.expression = annotation.text

    # Get segmentation
    segmentation = []
    trace_groups = root.findall("{http://www.w3.org/2003/InkML}traceGroup")
    if len(trace_groups) != 1:
        raise Exception(
            "Malformed InkML",
            (
                "Exactly 1 top level traceGroup expected, found %i. "
                "(%s) - probably no ground truth?"
            )
            % (len(trace_groups), filepath),
        )
    trace_group = trace_groups[0]
    symbol_stream = []  # has to be consistent with segmentation
    for tg in trace_group.findall("{http://www.w3.org/2003/InkML}traceGroup"):
        annotations = tg.findall("{http://www.w3.org/2003/InkML}annotation")
        if len(annotations) != 1:
            raise ValueError(
                "%i annotations found for '%s'." % (len(annotations), filepath)
            )
        db_id = formula_to_dbid(normalize_symbol_name(annotations[0].text))
        symbol_stream.append(db_id)
        trace_views = tg.findall("{http://www.w3.org/2003/InkML}traceView")
        symbol = []
        for traceView in trace_views:
            symbol.append(int(traceView.attrib["traceDataRef"]))
        segmentation.append(symbol)
    hw.symbol_stream = symbol_stream
    hw.segmentation = segmentation
    _flat_seg = [stroke2 for symbol2 in segmentation for stroke2 in symbol2]
    assert len(_flat_seg) == len(recording), (
        "Segmentation had length %i, but recording has %i strokes (%s)"
        % (len(_flat_seg), len(recording), filepath)
    )
    assert set(_flat_seg) == set(range(len(_flat_seg)))
    hw.inkml = beautify_xml(filepath)
    hw.filepath = filepath
    return hw


def read_folder(folder):
    """
    Parameters
    ----------
    folder : string
        Path to a folde with *.inkml files.

    Returns
    -------
    list :
        Objects of the type HandwrittenData
    """
    import glob

    recordings = []
    for filename in natsorted(glob.glob("%s/*.inkml" % folder)):
        hw = read(filename)
        if hw.formula_in_latex is not None:
            hw.formula_in_latex = hw.formula_in_latex.strip()
        if (
            hw.formula_in_latex is None
            or not hw.formula_in_latex.startswith("$")
            or not hw.formula_in_latex.endswith("$")
        ):
            if hw.formula_in_latex is not None:
                logging.info(
                    "Starts with: %s", str(hw.formula_in_latex.startswith("$"))
                )
                logging.info("ends with: %s", str(hw.formula_in_latex.endswith("$")))
            logging.info(hw.formula_in_latex)
            logging.info(hw.segmentation)
            hw.show()
        recordings.append(hw)
    return recordings


def main(folder):
    """
    Read folder.

    Parameters
    ----------
    folder : str
    """

    logging.info(folder)
    read_folder(folder)


def handler(signum, frame):
    """Add signal handler to savely quit program."""
    print("Signal handler called with signal %i" % signum)
    sys.exit(-1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handler)
    folder = (
        "/home/moose/Downloads/"
        "ICFHR_package/CROHME2011_data/CROHME_training/CROHME_training/"
    )
    main(folder)
