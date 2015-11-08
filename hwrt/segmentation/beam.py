#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import json
from copy import deepcopy
from functools import reduce  # Valid in Python 2.6+, required in Python 3
from decimal import Decimal, getcontext
getcontext().prec = 100

# hwrt modules
from .segmentation import single_clf
# from ..handwritten_data import HandwrittenData
# from .. import spacial_relationship
from .. import language_model
from ..utils import softmax

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

    def __init__(self, m=3, n=3, k=20):
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
        for hyp in self.hypotheses:
            new_geometry = deepcopy(hyp['geometry'])
            most_right = new_geometry
            if len(hyp['symbols']) == 0:
                while 'right' in most_right:
                    most_right = most_right['right']
                most_right['right'] = {'symbol_index': len(hyp['symbols']),
                                       'right': None}
            else:
                most_right = {'symbol_index': len(hyp['symbols']),
                              'right': None}
            for guess in guesses:
                sym = {'symbol': guess['semantics'],
                       'probability': guess['probability']}
                new_seg = deepcopy(hyp['segmentation'])
                new_seg.append([stroke_nr])
                new_sym = deepcopy(hyp['symbols'])
                new_sym.append(sym)
                b = {'segmentation': new_seg,
                     'symbols': new_sym,
                     'geometry': new_geometry,
                     'probability': reduce(getcontext().multiply,
                                           [Decimal(s['probability'])
                                            for s in new_sym],
                                           Decimal(1))
                     }

                # spacial_rels = []  # TODO
                # for s1_indices, s2_indices in zip(b['segmentation'],
                #                                   b['segmentation'][1:]):
                #     tmp = [new_beam.history['data'][el] for el in s1_indices]
                #     s1 = HandwrittenData(json.dumps(tmp))
                #     tmp = [new_beam.history['data'][el] for el in s2_indices]
                #     s2 = HandwrittenData(json.dumps(tmp))
                #     rel = spacial_relationship.estimate(s1, s2)
                #     spacial_rels.append(rel)
                # b['geometry'] = spacial_rels
                new_beam.hypotheses.append(b)

        # Get new guesses by assuming new_stroke belongs to an already begun
        # symbol
        for hyp in self.hypotheses:
            # Add stroke to last n symbols (seperately)
            for i in range(min(self.n, len(hyp['segmentation']))):
                # Build stroke data
                new_strokes = {'data': [], 'id': -1}
                for stroke_index in hyp['segmentation'][-(i+1)]:
                    curr_stroke = self.history['data'][stroke_index]
                    new_strokes['data'].append(curr_stroke)
                new_strokes['data'].append(new_stroke['data'][0])

                new_seg = deepcopy(hyp['segmentation'])
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
                    new_sym = deepcopy(hyp['symbols'])
                    new_sym[-(i+1)] = sym
                    b = {'segmentation': new_seg,
                         'symbols': new_sym,
                         'geometry': deepcopy(hyp['geometry']),
                         'probability': reduce(getcontext().multiply,
                                               [Decimal(s['probability'])
                                                for s in new_sym],
                                               Decimal(1))
                         }
                    new_beam.hypotheses.append(b)

        # Use language model to update probabilities
        lm_probs = []
        for hyp in new_beam.hypotheses:
            pure_symbols = [symbol['symbol'].split(";")[1]
                            for symbol in hyp['symbols']]
            pure_symbols = ["<s>"] + pure_symbols + ["</s>"]
            lm_prob = language_model.get_probability(pure_symbols)
            hyp['lm_probability'] = lm_prob
            lm_probs.append(lm_prob)

        new_probs = softmax([h['lm_probability']
                             for h in new_beam.hypotheses])
        # add = Decimal(1.0) - max(lm_probs)  # bring the highest one to 0.5
        for hyp, prob in zip(new_beam.hypotheses, new_probs):
            hyp['probability'] *= prob  # (hyp['lm_probability'])  # + add

        # Get probability again

        # for prob, hyp in zip(new_probs, new_beam.hypotheses):
        #     hyp['probability'] *= prob

        # Get geometry of each beam entry
        # TODO

        # Update probabilities
        # TODO

        self.hypotheses = new_beam.hypotheses
        self.history = new_beam.history
        self._prune()

    def _prune(self):
        """Shorten hypotheses to the best k ones."""
        self.hypotheses = sorted(self.hypotheses,
                                 key=lambda e: e['probability'],
                                 reverse=True)[:self.k]

    def get_results(self):
        results = []
        for hyp in self.hypotheses:
            results.append({'semantics': "-1;" + build_latex(hyp),
                            'probability': float(hyp['probability']),
                            'symbol count': len(hyp['segmentation'])})
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
