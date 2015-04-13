#!/usr/bin/env python

"""Testing script for write-math symbol classifier."""

import glob
import logging
import sys
import json
import pkg_resources
import os
import numpy

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)

# hwrt modules
from hwrt import HandwrittenData
from hwrt.classify import classify_segmented_recording as evaluate


def elementtree_to_dict(element):
    """Convert an xml ElementTree to a dictionary."""
    d = dict()
    if hasattr(element, 'text') and element.text is not None:
        d['text'] = element.text

    d.update(element.items())  # element's attributes

    for c in list(element):  # element's children
        if c.tag not in d:
            d[c.tag] = elementtree_to_dict(c)
        # an element with the same tag was already in the dict
        else:
            # if it's not a list already, convert it to a list and append
            if not isinstance(d[c.tag], list):
                d[c.tag] = [d[c.tag], elementtree_to_dict(c)]
           # append to the list
            else:
                d[c.tag].append(elementtree_to_dict(c))
    return d


def _less_than(l, n):
    """Get number of symbols in list `l` which have a value less than `n`.

    Parameters
    ----------
    l : list
        List of numbers
    n : int

    Returns
    -------
    float (with int values)
    """
    return float(len([1 for el in l if el < n]))


def strip_end(text, suffix):
    if not text.endswith(suffix):
        return text
    return text[:len(text)-len(suffix)]


def main(directory):
    recordings = []
    for filepath in glob.glob("%s/*.xml" % directory):
        import xml.etree.ElementTree
        root = xml.etree.ElementTree.parse(filepath).getroot()
        root = elementtree_to_dict(root)

        name = root['Name']['text']

        skip = ['frac', 'dt', 'dx', 'arcsin', 'cotg', 'tg', 'cross',
                '\cos', '\sin', '\ln', '\lim', "'",
                '\log', ',']
        if name in skip:
            continue

        replacements = [('int', r'\int'),
                        ('alpha', r'\alpha'),
                        ('beta', r'\beta'),
                        ('kappa', r'\kappa'),
                        ('inf', r'\infty'),
                        ('root', r'\sqrt{}'),
                        ('pi', r'\pi'),
                        ('{', '\{'),
                        ('}', '\}'),
                        ('leftSquareBracket', '['),
                        ('rightSquareBracket', ']'),
                        ('sum', r'\sum'),
                        ('prod', r'\prod'),
                        ('greater', r'>'),
                        ('greaterEqual', r'\geq'),
                        ('less', r'<'),
                        ('lessEqual', r'\leq'),
                        ('+-', r'\pm'),
                        ('lim', r'\lim'),
                        ('sin', r'\sin'),
                        ('cos', r'\cos'),
                        ('dot', r'\cdot'),  # really?
                        ('log', r'\log'),
                        ('ln', r'\ln'),
                        ('rightArrow', r'\rightarrow'),
                        ('verticalBar', r'||||'),
                        ('nabla', r'\nabla'),
                        ('partial', r'\partial'),
                        ('slash', r'/'),
                        ('star', r'\star'),
                        ('in', r'\in')]
        for search, rep in replacements:
            if name == search:
                name = name.replace(search, rep)

        if name in skip:
            continue

        name = strip_end(name, '_Capital')
        examples = root['Examples']['Example']
        logging.info("Name: %s", name)

        symbol_recordings = []

        #import pprint
        #pprint.pprint(root)
        if isinstance(examples, dict):
            examples = [examples]
        for example in examples:
            recording = []
            time = 0
            if isinstance(example['strokesXml']['Strokes']['Stroke'], dict):
                example['strokesXml']['Strokes']['Stroke'] = [example['strokesXml']['Strokes']['Stroke']]
            for stroke_xml in example['strokesXml']['Strokes']['Stroke']:
                stroke = []
                # print(stroke_xml.keys())
                if isinstance(stroke_xml['Point'], dict):
                    stroke_xml['Point'] = [stroke_xml['Point']]
                for point in stroke_xml['Point']:
                    stroke.append({'x': float(point['X']),
                                   'y': float(point['Y']),
                                   'time': time})
                    time += 20
                time += 200
                recording.append(stroke)
            hw = HandwrittenData.HandwrittenData(json.dumps(recording),
                                                 formula_in_latex=name)
            symbol_recordings.append(hw)
        recordings.append((name, symbol_recordings))
    return recordings


if __name__ == '__main__':
    recordings = main("/home/moose/Downloads/MfrDB_Symbols_v1.0")
    print(len(recordings))

    score_place = []
    symbols_showed = []
    for latex, symbol_recording in recordings:
        score_place_symbol = []
        for recording in symbol_recording:
            results = evaluate(json.dumps(recording.get_sorted_pointlist()),
                               result_format='LaTeX')
            for i, result in enumerate(results):
                if result['semantics'] == recording.formula_in_latex:
                    # if i > 5:
                    #     logging.info("  Found '%s' place %i with probability %0.4f.",
                    #                  recording.formula_in_latex,
                    #                  i,
                    #                  result['probability'])
                    #     if recording.formula_in_latex not in symbols_showed:
                    #         #recording.show()
                    #         symbols_showed.append(recording.formula_in_latex)
                    score_place.append(i)
                    score_place_symbol.append(i)
                    break
            else:
                if recording.formula_in_latex not in symbols_showed:
                    logging.info("#"*80)
                    logging.info(recording.formula_in_latex)
                    symbols_showed.append(recording.formula_in_latex)
        logging.info("{0:>10}: TOP-1: {1:0.2f} | TOP-3: {2:0.2f} | TOP-10: {3:0.2f} | TOP-50: {4:0.2f} | {5}".format(
                     latex,
                     _less_than(score_place_symbol, 1)/len(symbol_recording),
                     _less_than(score_place_symbol, 3)/len(symbol_recording),
                     _less_than(score_place_symbol, 10)/len(symbol_recording),
                     _less_than(score_place_symbol, 50)/len(symbol_recording),
                     len(symbol_recording)))

    total_recordings = len([1 for l, symb in recordings for el in symb])
    logging.info("mean place of correct classification: %0.2f",
                 numpy.mean(score_place))
    logging.info("median place of correct classification: %0.2f",
                 numpy.median(score_place))
    for i in [1, 3, 10, 20, 50]:
        logging.info("TOP-%i: %0.2f correct",
                     i,
                     _less_than(score_place, i)/total_recordings)
    #logging.info("Out of order: %i", out_of_order_count)
    logging.info("Total: %i", total_recordings)
