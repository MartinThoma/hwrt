#!/usr/bin/env python

"""
Utility functions and classes to deal with language models.
"""

# Core Library modules
import logging
import os
import tarfile
import tempfile
from decimal import Decimal, getcontext

# Third party modules
import pkg_resources

getcontext().prec = 100

ngram_model = None


class NgramLanguageModel:
    def __init__(self):
        self.ngrams = {}

    def load_from_arpa_str(self, arpa_str):
        """
        Initialize N-gram model by reading an ARPA language model string.

        Parameters
        ----------
        arpa_str : str
            A string in ARPA language model file format
        """
        data_found = False
        end_found = False
        in_ngram_block = 0
        for i, line in enumerate(arpa_str.split("\n")):
            if not end_found:
                if not data_found:
                    if "\\data\\" in line:
                        data_found = True
                else:
                    if in_ngram_block == 0:
                        if line.startswith("ngram"):
                            ngram_type, count = line.split("=")
                            _, n = ngram_type.split(" ")
                            n = int(n)
                            self.ngrams[n] = {"data": {}, "count": count}
                        elif line.startswith("\\"):
                            n = int(line.split("-")[0][1:])
                            in_ngram_block = n
                        else:
                            continue  # Empty line
                    elif in_ngram_block > 0:
                        if "\\end\\" in line:
                            end_found = True
                        elif line.startswith("\\"):
                            n = int(line.split("-")[0][1:])
                            in_ngram_block = n
                        elif len(line) <= 1:
                            continue
                        else:
                            data = line.split("\t")
                            probability = Decimal(data[0])
                            ngram = data[1:]
                            if len(ngram) != n:
                                raise Exception(
                                    (
                                        "ARPA language file is "
                                        "inconsistant. Line %i has "
                                        "only %i items, but should "
                                        "have %i items."
                                    )
                                    % (i, len(ngram), n)
                                )
                            rest = ngram
                            append_to = self.ngrams[n]["data"]
                            while len(rest) > 1:
                                first, rest = rest[0], rest[1:]
                                if first not in append_to:
                                    append_to[first] = {}
                                append_to = append_to[first]
                            if rest[0] in append_to:
                                raise Exception(
                                    ("Duplicate entry for " "ngram %s") % ngram
                                )
                            append_to[rest[0]] = probability
            else:
                if line.startswith("info: "):
                    logging.info(line[6:])

    def get_unigram_log_prob(self, unigram):
        w1 = unigram[0]
        if w1 in self.ngrams[1]["data"]:
            return self.ngrams[1]["data"][w1]
        return Decimal(int(self.ngrams[1]["count"]["<unk>"]))

    def get_bigram_log_prob(self, bigram):
        w1, w2 = bigram
        if w1 in self.ngrams[2]["data"]:
            if w2 in self.ngrams[2]["data"][w1]:
                return self.ngrams[2]["data"][w1][w2]
        return Decimal(1.0).log10() - Decimal(int(self.ngrams[1]["count"])).log10()

    def get_trigram_log_prob(self, trigram):
        """
        Calcualate the probability P(w1, w2, w3), given this language model.

        Parameters
        ----------
        trigram
            tuple with exactly 3 elements

        Returns
        -------
        numeric
            The log likelihood of P(w3 | (w1, w2))
        """
        w1, w2, w3 = trigram
        # if w1 not in self.ngrams[1]['data']:
        #     w1 = "<unk>"
        # if w2 not in self.ngrams[1]['data']:
        #     w2 = "<unk>"
        # if w3 not in self.ngrams[1]['data']:
        #     w3 = "<unk>"
        if w1 in self.ngrams[3]["data"]:
            if w2 in self.ngrams[3]["data"][w1]:
                if w3 in self.ngrams[3]["data"][w1][w2]:
                    return self.ngrams[3]["data"][w1][w2][w3]
        return Decimal(1.0).log10() - Decimal(int(self.ngrams[1]["count"]) ** 2).log10()

    def get_probability(self, sentence):
        """
        Calculate the probability of a sentence, given this language model.

        Get P(sentence) = P(w1, w2, w3, ..., wn)
                        = P(w1, w2, w3) * P(w2, w3, w4) *...* P(wn-2, wn-1, wn)
        Parameters
        ----------
        sentence : list
            A list of strings / tokens.
        """
        if len(sentence) == 1:
            return Decimal(10) ** self.get_unigram_log_prob(sentence)
        elif len(sentence) == 2:
            return Decimal(10) ** self.get_bigram_log_prob(sentence)
        else:
            log_prob = Decimal(0.0)
            for w1, w2, w3 in zip(sentence, sentence[1:], sentence[2:]):
                log_prob += self.get_trigram_log_prob((w1, w2, w3))
            log_prob = Decimal(log_prob)
            return Decimal(10) ** log_prob

    def print_all(self):
        for n, data in sorted(list(self.ngrams.items()), key=lambda n: n[0]):
            print("n=%i" % n)
            for key, value in data["data"].items():
                print(f"{key}\t{value}")


def load_model():
    """
    Load a n-gram language model for mathematics in ARPA format which gets
    shipped with hwrt.

    Returns
    -------
    A NgramLanguageModel object
    """
    logging.info("Load language model...")
    ngram_arpa_t = pkg_resources.resource_filename("hwrt", "misc/ngram.arpa.tar.bz2")
    with tarfile.open(ngram_arpa_t, "r:bz2") as tar:
        tarfolder = tempfile.mkdtemp()
        tar.extractall(path=tarfolder)
    ngram_arpa_f = os.path.join(tarfolder, "ngram.arpa")
    with open(ngram_arpa_f) as f:
        content = f.read()
    ngram_model = NgramLanguageModel()
    ngram_model.load_from_arpa_str(content)
    return ngram_model


def get_probability(sentence):
    global ngram_model
    if ngram_model is None:
        initialize_module()
    return ngram_model.get_probability(sentence)


def get_parser():
    """Return the parser object for this script."""
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

    parser = ArgumentParser(
        description=__doc__, formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-s", "--sentence", dest="sentence", help="sentence, splitted by ';'"
    )
    return parser


def initialize_module():
    """
    Initialize the language model module.

    This loads the language model.
    """
    global ngram_model
    ngram_model = load_model()


if __name__ == "__main__":
    args = get_parser().parse_args()
    sentence = args.sentence.split(";")
    print("Sentence s=%s" % sentence)
    print("P(s) = %0.12f" % get_probability(sentence))
