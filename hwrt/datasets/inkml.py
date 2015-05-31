#!/usr/bin/env python

import json
import signal
import sys
import logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)

from natsort import natsorted
from xml.dom.minidom import parseString

# hwrt modules
from hwrt import HandwrittenData
from hwrt.datasets import formula_to_dbid


def beautify_xml(path):
    """Beautify / pretty print XML in `path`."""
    with open(path) as f:
        content = f.read()

    pretty_print = lambda data: '\n'.join([line for line in parseString(data).toprettyxml(indent=' '*2).split('\n') if line.strip()])
    return pretty_print(content)


def normalize_symbol_name(symbol_name):
    if symbol_name == '\\frac':
        return '\\frac{}{}'
    elif symbol_name == '\\sqrt':
        return '\\sqrt{}'
    elif symbol_name == '&lt;':
        return '<'
    elif symbol_name == '&gt;':
        return '>'
    elif symbol_name == '{':
        return '\{'
    elif symbol_name == '}':
        return '\}'
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
    strokes = sorted(root.findall('{http://www.w3.org/2003/InkML}trace'),
                     key=lambda child: child.attrib['id'])
    time = 0
    for stroke in strokes:
        stroke = stroke.text.strip().split(',')
        stroke = [point.strip().split(' ') for point in stroke]
        if len(stroke[0]) == 3:
            stroke = [{'x': float(x), 'y': float(y), 'time': float(t)}
                      for x, y, t in stroke]
        else:
            stroke = [{'x': float(x), 'y': float(y)} for x, y in stroke]
            new_stroke = []
            for p in stroke:
                new_stroke.append({'x': p['x'], 'y': p['y'], 'time': time})
                time += 20
            stroke = new_stroke
            time += 200
        recording.append(stroke)

    # Get LaTeX
    formula_in_latex = None
    # TODO: Make sure the order is correct!!!!!
    annotations = root.findall('{http://www.w3.org/2003/InkML}annotation')
    for annotation in annotations:
        if annotation.attrib['type'] == 'truth':
            formula_in_latex = annotation.text
    hw = HandwrittenData.HandwrittenData(json.dumps(recording),
                                         formula_in_latex=formula_in_latex)
    for annotation in annotations:
        if annotation.attrib['type'] == 'writer':
            hw.writer = annotation.text
        elif annotation.attrib['type'] == 'category':
            hw.category = annotation.text
        elif annotation.attrib['type'] == 'expression':
            hw.expression = annotation.text

    # Get segmentation
    segmentation = []
    # TODO: Make sure the order is correct!!!!!
    traceGroups = root.findall('{http://www.w3.org/2003/InkML}traceGroup')
    if len(traceGroups) != 1:
        raise Exception('Malformed InkML',
                        'Exactly 1 top level traceGroup expected, found %i.' %
                        len(traceGroups))
    traceGroup = traceGroups[0]
    symbol_stream = []  # has to be consistent with segmentation
    # TODO: Make sure the order is correct!!!!!
    for tg in traceGroup.findall('{http://www.w3.org/2003/InkML}traceGroup'):
        annotations = tg.findall('{http://www.w3.org/2003/InkML}annotation')
        if len(annotations) != 1:
            raise ValueError("%i annotations found for '%s'." %
                             (len(annotations), filepath))
        symbol_stream.append(formula_to_dbid(normalize_symbol_name(annotations[0].text)))
        traceViews = tg.findall('{http://www.w3.org/2003/InkML}traceView')
        symbol = []
        for traceView in traceViews:
            symbol.append(int(traceView.attrib['traceDataRef']))
        segmentation.append(symbol)
    hw.symbol_stream = symbol_stream
    hw.segmentation = segmentation
    _flat_seg = [stroke for symbol in segmentation for stroke in symbol]
    assert len(_flat_seg) == len(recording), \
        ("Segmentation had length %i, but recording has %i strokes" %
         (len(_flat_seg), len(recording)))
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
        #logging.info(filename)
        hw = read(filename)
        if hw.formula_in_latex is not None:
            hw.formula_in_latex = hw.formula_in_latex.strip()
        if hw.formula_in_latex is None or not hw.formula_in_latex.startswith('$') or not hw.formula_in_latex.endswith('$'):
            if hw.formula_in_latex is not None:
                logging.info("Starts with: %s", str(hw.formula_in_latex.startswith('$')))
                logging.info("ends with: %s", str(hw.formula_in_latex.endswith('$')))
            logging.info(hw.formula_in_latex)
            logging.info(hw.segmentation)
            hw.show()
        recordings.append(hw)
    return recordings


def main():
    #hw = read("misc/IVC_learn/f1e1.inkml")
    #hw.show()

    folder = "/home/moose/Downloads/ICFHR_package/CROHME2011_data/CROHME_training/CROHME_training/"
    logging.info(folder)
    read_folder(folder)


def handler(signum, frame):
    print('Signal handler called with signal %i' % signum)
    sys.exit(-1)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler)
    main()
