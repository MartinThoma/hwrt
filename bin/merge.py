#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Merge two raw data pickle files."""

import pickle

from hwrt.utils import is_valid_file


def main(dataset1, dataset2, target):
    """
    Parameters
    ----------
    dataset1 : str
    dataset2 : str
    target : str
    """
    d1 = read_raw(dataset1)
    d2 = read_raw(dataset2)
    merged = merge(d1, d2)
    with open(target, 'wb') as f:
        pickle.dump(merged, f, protocol=pickle.HIGHEST_PROTOCOL)


def read_raw(data_path):
    """
    Parameters
    ----------
    data_path : str
    """
    with open(data_path, 'rb') as f:
        data = pickle.load(f)
    return data


def merge(d1, d2):
    """Merge two raw datasets into one.

    Parameters
    ----------
    d1 : dict
    d2 : dict

    Returns
    -------
    dict
    """
    formula_id2latex = d1['formula_id2latex'].copy()
    print(formula_id2latex)
    formula_id2latex.update(d2['formula_id2latex'])
    handwriting_datasets = d1['handwriting_datasets']
    for dataset in d2['handwriting_datasets']:
        handwriting_datasets.append(handwriting_datasets)
    return {'formula_id2latex': formula_id2latex,
            'handwriting_datasets': handwriting_datasets}


def get_parser():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d1",
                        dest="d1",
                        type=lambda x: is_valid_file(parser, x),
                        help="dataset 1",
                        metavar="FILE",
                        required=True)
    parser.add_argument("-d2",
                        dest="d2",
                        type=lambda x: is_valid_file(parser, x),
                        help="dataset 2",
                        metavar="FILE",
                        required=True)
    parser.add_argument("-t", "--target",
                        dest="target",
                        help="target",
                        metavar="FILE",
                        required=True)
    return parser


if __name__ == "__main__":
    args = get_parser().parse_args()
    main(args.d1, args.d2, args.target)
