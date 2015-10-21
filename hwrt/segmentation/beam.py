#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import time
from copy import deepcopy
from functools import reduce  # Valid in Python 2.6+, required in Python 3
from decimal import Decimal, getcontext
getcontext().prec = 100

# hwrt modules
from .segmentation import single_clf
from ..handwritten_data import HandwrittenData
from .. import spacial_relationship
from .. import language_model

__all__ = [
    "Beam"
]


class Beam(object):
    """

    Parameters
    ----------
    m : int, >= 1
        Number of symbols which get considered. This determines how many
        new segmentations come, where `new_stroke` belongs to a new symbol.
    n : int, >= 1
        Number of strokes to which `new_stroke` will be added.
        This determines how many new segmentations come, where `new_stroke`
        belongs to an old symbol.
    k : int, >= 1
        Maximum number of elements in the beam.

    Attributes
    ----------
    hypotheses : list of dicts
        [{'segmentation': [[0, 3], [1, 2]],
          'symbols': [{'symbol': ID, 'probability': 0.12}],
          'geometry': {'symbol': index,
                       'bottom': None or dict,
                       'subscript': None or dict,
                       'right': None or dict,
                       'superscript': None or dict,
                       'top': None or dict},
           'LM': ???,
           'probability': 0.123
         }, ...]
    history: dict
        {'data': [[{'x': 12, 'y': 34, 'time': 56}, ...],
                  ...,
                  ],
         'id': -1}
         }
    """

    def __init__(self, m=10, n=3, k=50):
        self.m = m
        self.n = n
        self.k = k
        self.history = {'data': [], 'id': -1}
        self.hypotheses = []

    def add_stroke(self, new_stroke):
        """
        Update the beam so that it considers `new_stroke`.

        When a `new_stroke` comes, it can either belong to a symbol for which
        at least one other stroke was already made or belong to a symbol for
        which `new_stroke` is the first stroke.

        The number of hypotheses after q strokes without pruning is

            f: N_0 -> N_0
            f(0) = 1
            f(1) = m
            f(q) = f(q-1)*(m+n)

        The number of time the single symbol classifier has to be called, when
        already q hypotheses exist:

            f_s: N_0 -> N_0
            f_s(q) = q*n + 1 (upper bound)

        Parameters
        ----------
        new_stroke : list of dicts
            A list of dicts {'x': 12, 'y': 34, 'time': 56} which represent a
            point.
        """
        global single_clf
        t0 = time.time()
        if len(self.hypotheses) == 0:  # Don't put this in the constructor!
            self.hypotheses = [{'segmentation': [],
                                'symbols': [],
                                'geometry': {},
                                'probability': Decimal(1)
                                }]
        stroke_nr = len(self.history['data'])
        new_history = deepcopy(self.history)
        new_history['data'].append(new_stroke['data'][0])
        new_beam = Beam()
        new_beam.history = new_history

        evaluated_segmentations = []

        # Get new guesses by assuming new_stroke is a new symbol
        guesses = single_clf.predict(new_stroke)[:self.m]
        for hypothesis in self.hypotheses:
            new_geometry = deepcopy(hypothesis['geometry'])
            most_right = new_geometry
            if len(hypothesis['symbols']) == 0:
                while 'right' in most_right:
                    most_right = most_right['right']
                most_right['right'] = {'symbol_index': len(hypothesis['symbols']),
                                       'right': None}
            else:
                most_right = {'symbol_index': len(hypothesis['symbols']),
                              'right': None}
            for guess in guesses:
                sym = {'symbol': guess['semantics'],
                       'probability': guess['probability']}
                new_seg = deepcopy(hypothesis['segmentation'])
                new_seg.append([stroke_nr])
                new_sym = deepcopy(hypothesis['symbols'])
                new_sym.append(sym)
                b = {'segmentation': new_seg,
                     'symbols': new_sym,
                     'geometry': new_geometry,
                     'probability': reduce(getcontext().multiply,
                                           [Decimal(s['probability']) for s in new_sym],
                                           Decimal(1))
                     }

                spacial_rels = []  # TODO
                for s1_indices, s2_indices in zip(b['segmentation'],
                                                  b['segmentation'][1:]):
                    s1 = HandwrittenData(json.dumps([new_beam.history['data'][el] for el in s1_indices]))
                    s2 = HandwrittenData(json.dumps([new_beam.history['data'][el] for el in s2_indices]))
                    rel = spacial_relationship.estimate(s1, s2)
                    spacial_rels.append(rel)
                b['geometry'] = spacial_rels
                new_beam.hypotheses.append(b)
        t1 = time.time()

        # Get new guesses by assuming new_stroke belongs to an already begun
        # symbol
        for hypothesis in self.hypotheses:
            # Add stroke to last n symbols (seperately)
            for i in range(min(self.n, len(hypothesis['segmentation']))):
                # Build stroke data
                new_strokes = {'data': [], 'id': -1}
                for stroke_index in hypothesis['segmentation'][-(i+1)]:
                    new_strokes['data'].append(self.history['data'][stroke_index])
                new_strokes['data'].append(new_stroke['data'][0])

                new_seg = deepcopy(hypothesis['segmentation'])
                new_seg[-(i+1)].append(stroke_nr)

                if new_seg in evaluated_segmentations:
                    continue
                else:
                    evaluated_segmentations.append(new_seg)

                # Predict this new collection of strokes
                guesses = single_clf.predict(new_strokes)[:self.m]
                for guess in guesses:
                    sym = {'symbol': guess['semantics'],
                           'probability': guess['probability']}
                    new_sym = deepcopy(hypothesis['symbols'])
                    new_sym[-(i+1)] = sym
                    b = {'segmentation': new_seg,
                         'symbols': new_sym,
                         'geometry': deepcopy(hypothesis['geometry']),
                         'probability': reduce(getcontext().multiply,
                                               [Decimal(s['probability']) for s in new_sym],
                                               Decimal(1))
                         }
                    new_beam.hypotheses.append(b)

        # Use language model to update probabilities
        lm_probs = []
        for hypothesis in new_beam.hypotheses:
            pure_symbols = [symbol['symbol'].split(";")[1]
                            for symbol in hypothesis['symbols']]
            pure_symbols = ["<s>"] + pure_symbols + ["</s>"]
            lm_prob = language_model.get_probability(pure_symbols)
            hypothesis['lm_probability'] = lm_prob
            lm_probs.append(lm_prob)
        add = Decimal(1.0) - max(lm_probs)  # bring the highest one to 0.5
        for hypothesis in new_beam.hypotheses:
            hypothesis['probability'] *= (hypothesis['lm_probability'] + add)

        # Get probability again
        # new_probs = softmax([h['lm_probability'] for h in new_beam.hypotheses])
        # for prob, hypothesis in zip(new_probs, new_beam.hypotheses):
        #     hypothesis['probability'] *= prob

        # Get geometry of each beam entry
        # TODO

        # Update probabilities
        # TODO

        self.hypotheses = new_beam.hypotheses
        self.history = new_beam.history
        self._prune()
        t2 = time.time()
        logging.info("It took %0.3fs to add this stroke.", (t2-t0))
        logging.info("%0.3fs for the first part, %0.3fs for the second",
                     (t1-t0),
                     (t2-t1))

    def _prune(self):
        """Shorten hypotheses to the best k ones."""
        self.hypotheses = sorted(self.hypotheses,
                                 key=lambda e: e['probability'],
                                 reverse=True)[:self.k]

    def get_results(self):
        results = []
        for hyp in self.hypotheses:
            results.append({'semantics': "-1;" + build_latex(hyp),
                            'probability': float(hyp['probability'])})
        return results

    def __str__(self):
        s = "Beam(n=%i, m=%i, k=%i)\n" % (self.n, self.m, self.k)
        for hyp in self.hypotheses:
            symbols = [el['symbol'] for el in hyp['symbols']]
            symbols = str([el.split(';')[1] for el in symbols])
            s += "\t%0.3f%%\t%s\n" % (hyp['probability']*100, symbols)
        return s


def build_latex(hyp):
    """
    Parameters
    ----------
    hyp : dict
        {'segmentation': [[0, 3], [1, 2]],
         'symbols': [{'symbol': ID, 'probability': 0.12}],
         'geometry': {'symbol': index,
                      'bottom': None or dict,
                      'subscript': None or dict,
                      'right': None or dict,
                      'superscript': None or dict,
                      'top': None or dict},
          'LM': ???,
          'probability': 0.123
        }
    """
    latex = []
    for symbol in hyp['symbols']:
        latex.append(symbol['symbol'].split(";")[1])
    return " ".join(latex)
