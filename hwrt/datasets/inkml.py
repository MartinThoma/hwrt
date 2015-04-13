#!/usr/bin/env python

import json
import signal
import sys
import logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)

# hwrt modules
from hwrt import HandwrittenData


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
        stroke = [{'x': float(x), 'y': float(y)} for x, y in stroke]
        new_stroke = []
        for p in stroke:
            new_stroke.append({'x': p['x'], 'y': p['y'], 'time': time})
            time += 20
        recording.append(new_stroke)
        time += 200

    # Get LaTeX
    formula_in_latex = None
    annotations = root.findall('{http://www.w3.org/2003/InkML}annotation')
    for annotation in annotations:
        if annotation.attrib['type'] == 'truth':
            formula_in_latex = annotation.text
    hw = HandwrittenData.HandwrittenData(json.dumps(recording),
                                         formula_in_latex=formula_in_latex)

    # Get segmentation
    # segmentation = []
    # traceGroups = root.findall('{http://www.w3.org/2003/InkML}traceGroup')
    # if len(traceGroups) != 1:
    #     raise Exception('Malformed InkML',
    #                     'Exactly 1 top level traceGroup expected, found %i.' %
    #                     len(traceGroups))
    # traceGroup = traceGroups[0]
    # for tg in traceGroup.findall('{http://www.w3.org/2003/InkML}traceGroup'):
    #     traceViews = tg.findall('{http://www.w3.org/2003/InkML}traceView')
    #     symbol = []
    #     for traceView in traceViews:
    #         symbol.append(int(traceView.attrib['traceDataRef']))
    #     segmentation.append(symbol)
    # hw.segmentation = segmentation
    # _flat_seg = [stroke for symbol in segmentation for stroke in symbol]
    # assert len(_flat_seg) == len(recording), \
    #     ("Segmentation had length %i, but recording has %i strokes" %
    #      (len(_flat_seg), len(recording)))
    # assert set(_flat_seg) == set(range(len(_flat_seg)))

    return hw


def read_folder(folder):
    import glob
    for filename in glob.glob("%s/*.inkml" % folder):
        logging.info(filename)
        hw = read(filename)
        logging.info(hw.formula_in_latex)
        #hw.show()


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
