#!/usr/bin/env python

import glob
import logging
import sys
import json

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)

import pymysql
import pymysql.cursors
import unicodedata

# hwrt modules
from hwrt import HandwrittenData
from hwrt import utils
from hwrt import datasets

replacements = [('int', r'\int'),
                ('cross', r'\times'),
                ('frac', r'\frac{}{}'),
                ('sin', r'\sin'),
                ('dx', r'\mathrm{d}x'),
                ('dt', r'\mathrm{d}t'),
                ('arcsin', r'\arcsin'),
                ('cos', r'\cos'),
                ('lim', r'\lim'),
                ('log', r'\log'),
                ('ln', r'\ln'),
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
                ('verticalBar', r'|'),
                ('nabla', r'\nabla'),
                ('partial', r'\partial'),
                ('slash', r'/'),
                ('star', r'\star'),
                ('in', r'\in')]

skip = ['cotg']
# skip = ['frac', 'dt', 'dx', 'arcsin',  'tg', 'cross', "'", ',']
# '\sin', '\cos', '\lim', '\log', '\ln'


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


def strip_end(text, suffix):
    """Strip `suffix` from the end of `text` if `text` has that suffix."""
    if not text.endswith(suffix):
        return text
    return text[:len(text)-len(suffix)]


def remove_accents(input_str):
    nkfd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])


def get_recordings(directory):
    recordings = []
    for filepath in glob.glob("%s/*.xml" % directory):
        import xml.etree.ElementTree
        root = xml.etree.ElementTree.parse(filepath).getroot()
        root = elementtree_to_dict(root)

        name = root['Name']['text']

        if name in skip:
            continue

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
                example['strokesXml']['Strokes']['Stroke'] = \
                    [example['strokesXml']['Strokes']['Stroke']]
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
            info = {}
            if 'text' in example['FormulaInputInfo']['Username']:
                uname = example['FormulaInputInfo']['Username']['text'].strip()
                info['username'] = 'MfrDB::%s' % remove_accents(unicode(uname))
                info['username'] = info['username'].replace("+", "PLUS")
                info['username'] = info['username'].replace("...", "DOTS")
                info['username'] = info['username'].replace(u"\u0432\u044b\u0444", "BBEF")
                info['username'] = info['username'].replace(u"\u0437\u0438\u0438", "Zeii")
            else:
                info['username'] = 'MfrDB::unknown'
            copyright_str = ("This dataset was contributed by MfrDB. You can "
                             "download their complete dataset at "
                             "[mfr.felk.cvut.cz/Database.html]"
                             "(http://mfr.felk.cvut.cz/Database.html)")
            info['userid'] = datasets.getuserid(info['username'],
                                                copyright_str)
            import uuid
            info['secret'] = str(uuid.uuid4())
            info['ip'] = example['FormulaInputInfo']['Address']['text']
            import IPy
            info['ip'] = IPy.IP(info['ip']).int()
            info['accepted_formula_id'] = datasets.formula_to_dbid(name)
            info['client'] = example['FormulaInputInfo']['Client']['text']
            from dateutil.parser import parse
            info['creation_date'] = parse(example['FormulaInputInfo']['Time']['text'])
            info['device_type'] = example['FormulaInputInfo']['Device']['text'].lower()
            info['sample_id'] = example['FormulaInputInfo']['SampleId']['text']
            info['rec_desc'] = "%s::%s::%s::%s::%s" % (filepath,
                                                       example['Id'],
                                                       info['sample_id'],
                                                       info['client'],
                                                       example['FormulaInputInfo']['Address']['text'])
            info['description'] = ("This dataset was contributed by MfrDB. "
                                   "You can download their complete dataset "
                                   "at [mfr.felk.cvut.cz/Database.html](http://mfr.felk.cvut.cz/Database.html)")
            symbol_recordings.append((hw, info))
        recordings.append((name, symbol_recordings))
    return recordings
