#!/usr/bin/env python

# Core Library modules
import logging
import os
import sys
from copy import deepcopy
from decimal import Decimal, getcontext

# Third party modules
import pkg_resources
import yaml

# Local modules
# from ..handwritten_data import HandwrittenData
# from .. import spacial_relationship
from .. import language_model
from ..utils import softmax
from .segmentation import single_clf

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.DEBUG,
    stream=sys.stdout,
)

getcontext().prec = 100


__all__ = ["Beam"]


stroke_prob = None


def p_strokes(symbol: str, count: int) -> float:
    """
    Get the probability of a written `symbol` having `count` strokes.

    Parameters
    ----------
    symbol : str
        LaTeX command
    count : int, >= 1

    Returns
    -------
    epsilon : float
        In [0.0, 1.0]
    """
    global stroke_prob
    assert count >= 1
    epsilon = 0.00000001
    if stroke_prob is None:
        misc_path = pkg_resources.resource_filename("hwrt", "misc/")
        stroke_prob_file = os.path.join(misc_path, "prob_stroke_count_by_symbol.yml")
        with open(stroke_prob_file) as stream:
            stroke_prob = yaml.safe_load(stream)
    if symbol in stroke_prob:
        if count in stroke_prob[symbol]:
            return stroke_prob[symbol][count]
        else:
            return epsilon
    return epsilon


def _calc_hypothesis_probability(hypothesis):
    """
    Get the probability (or rather a score) of a hypothesis.

    Parameters
    ----------
    hypothesis : dict
        with keys 'segmentation', 'symbols', ...

    Returns
    -------
    float
        in [0.0, 1.0]
    """
    prob = 0.0
    for symbol, seg in zip(hypothesis["symbols"], hypothesis["segmentation"]):
        # symbol_latex = symbol['symbol'].split(";")[1]
        # TODO: Does p_strokes really improve the system?
        prob += symbol["probability"]  # * p_strokes(symbol_latex, len(seg))

    # Use language model to update probabilities
    pure_symbols = [symbol["symbol"].split(";")[1] for symbol in hypothesis["symbols"]]
    pure_symbols = ["<s>"] + pure_symbols + ["</s>"]
    lm_prob = language_model.get_probability(pure_symbols)
    hypothesis["lm_probability"] = 2 ** lm_prob
    return (
        prob
        * float(hypothesis["lm_probability"])
        * (1.0 / len(hypothesis["segmentation"]))
    )


class Beam:
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
           'probability': 0.123
         }, ...]
    history: dict
        {'data': [[{'x': 12, 'y': 34, 'time': 56}, ...],
                  ...,
                  ],
         'id': -1}
         }
    """

    def __init__(self, m=10, n=1, k=20):
        self.m = m
        self.n = n
        self.k = k
        self.history = {"data": [], "id": -1}
        self.hypotheses = []

    def _add_hypotheses_assuming_new_stroke(self, new_stroke, stroke_nr, new_beam):
        """
        Get new guesses by assuming new_stroke is a new symbol.

        Parameters
        ----------
        new_stroke : list of dicts
            A list of dicts [{'x': 12, 'y': 34, 'time': 56}, ...] which
            represent a point.
        stroke_nr : int
            Number of the stroke for segmentation
        new_beam : beam object
        """
        guesses = single_clf.predict({"data": [new_stroke], "id": None})[: self.m]
        for hyp in self.hypotheses:
            new_geometry = deepcopy(hyp["geometry"])
            most_right = new_geometry
            if len(hyp["symbols"]) == 0:
                while "right" in most_right:
                    most_right = most_right["right"]
                most_right["right"] = {
                    "symbol_index": len(hyp["symbols"]),
                    "right": None,
                }
            else:
                most_right = {"symbol_index": len(hyp["symbols"]), "right": None}
            for guess in guesses:
                sym = {
                    "symbol": guess["semantics"],
                    "probability": guess["probability"],
                }
                new_seg = deepcopy(hyp["segmentation"])
                new_seg.append([stroke_nr])
                new_sym = deepcopy(hyp["symbols"])
                new_sym.append(sym)
                b = {
                    "segmentation": new_seg,
                    "symbols": new_sym,
                    "geometry": new_geometry,
                    "probability": None,
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
            A list of dicts [{'x': 12, 'y': 34, 'time': 56}, ...] which
            represent a point.
        """
        global single_clf
        if len(self.hypotheses) == 0:  # Don't put this in the constructor!
            self.hypotheses = [
                {
                    "segmentation": [],
                    "symbols": [],
                    "geometry": {},
                    "probability": Decimal(1),
                }
            ]
        stroke_nr = len(self.history["data"])
        new_history = deepcopy(self.history)
        new_history["data"].append(new_stroke)
        new_beam = Beam()
        new_beam.history = new_history

        evaluated_segmentations = []

        # Get new guesses by assuming new_stroke belongs to an already begun
        # symbol
        had_multisymbol = False
        for hyp in self.hypotheses:
            # Add stroke to last n symbols (seperately)
            for i in range(min(self.n, len(hyp["segmentation"]))):
                # Build stroke data
                new_strokes = {"data": [], "id": -1}
                for stroke_index in hyp["segmentation"][-(i + 1)]:
                    curr_stroke = self.history["data"][stroke_index]
                    new_strokes["data"].append(curr_stroke)
                new_strokes["data"].append(new_stroke)

                new_seg = deepcopy(hyp["segmentation"])
                new_seg[-(i + 1)].append(stroke_nr)

                if new_seg in evaluated_segmentations:
                    continue
                else:
                    evaluated_segmentations.append(new_seg)

                # Predict this new collection of strokes
                guesses = single_clf.predict(new_strokes)[: self.m]
                for guess in guesses:
                    if guess["semantics"].split(";")[1] == "::MULTISYMBOL::":
                        # This was a wrong segmentation. Ignore it.
                        had_multisymbol = True
                        continue
                    sym = {
                        "symbol": guess["semantics"],
                        "probability": guess["probability"],
                    }
                    new_sym = deepcopy(hyp["symbols"])
                    new_sym[-(i + 1)] = sym
                    b = {
                        "segmentation": new_seg,
                        "symbols": new_sym,
                        "geometry": deepcopy(hyp["geometry"]),
                        "probability": None,
                    }
                    new_beam.hypotheses.append(b)

        if len(self.hypotheses) <= 1 or had_multisymbol:
            self._add_hypotheses_assuming_new_stroke(new_stroke, stroke_nr, new_beam)

        for hyp in new_beam.hypotheses:
            hyp["probability"] = _calc_hypothesis_probability(hyp)

        # Get probability again

        # Get geometry of each beam entry
        # TODO

        # Update probabilities
        # TODO

        # Normalize to sum=1
        self.hypotheses = new_beam.hypotheses
        self.history = new_beam.history
        self._prune()
        new_probs = softmax([h["probability"] for h in self.hypotheses])
        for hyp, prob in zip(self.hypotheses, new_probs):
            hyp["probability"] = prob

    def _prune(self):
        """Shorten hypotheses to the best k ones."""
        self.hypotheses = sorted(
            self.hypotheses, key=lambda e: e["probability"], reverse=True
        )[: self.k]

    def get_results(self):
        results = []
        for hyp in self.hypotheses:
            results.append(
                {
                    "semantics": build_unicode(hyp),
                    "complete_latex": build_latex(hyp),
                    "probability": float(hyp["probability"]),
                    "symbol count": len(hyp["segmentation"]),
                }
            )
        return results

    def get_writemath_results(self):
        """
        Get the result in the format
        [{'probability': 0.987,
          'segmentation': [[0, 1], [2, 4], [3]]}   // index of the stroke
          'symbols': [{'id': 456,  // on write-math.com
                       'probability': 0.123},
                      {'id': 456,
                       'probability': 0.999},  // The sum does not have to be 1
                      {'id': 195,
                       'probability': 0.0001}]
          },
         {...}  // another hypothesis
        ]
        """
        results = []
        for hyp in self.hypotheses:
            symbols = []
            for sym in hyp["symbols"]:
                symbols.append(
                    {
                        "id": sym["symbol"].split(";")[0],
                        "probability": sym["probability"],
                    }
                )
            results.append(
                {
                    "probability": float(hyp["probability"]),
                    "segmentation": hyp["segmentation"],
                    "symbols": symbols,
                }
            )
        return results

    def __str__(self):
        s = "Beam(n=%i, m=%i, k=%i)\n" % (self.n, self.m, self.k)
        for hyp in self.hypotheses:
            symbols = [sym["symbol"] for sym in hyp["symbols"]]
            symbols = str([sym.split(";")[1] for sym in symbols])
            s += f"\t{hyp['probability'] * 100:0.3f}%\t{symbols}\n"
        return s


def build_unicode(hyp):
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
          'probability': 0.123
        }
    """
    latex = []
    for symbol in hyp["symbols"]:
        latex.append(symbol["symbol"])
    return ";;".join(latex)


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
          'probability': 0.123
        }
    """
    latex = []
    for symbol in hyp["symbols"]:
        latex.append(symbol["symbol"].split(";")[1])
    return " ".join(latex)
