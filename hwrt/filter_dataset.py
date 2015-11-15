#!/usr/bin/env python

"""
Given a dataset and a vocabulary file, filter the recordings which are desired.
"""

# This has to work with preprocess_dataset.py
import pkg_resources
import os
import csv
import yaml
try:  # Python 2
    import cPickle as pickle
except ImportError:  # Python 3
    import pickle
import sys
import logging
from natsort import natsorted

# hwrt modules
from . import utils


logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)


def main(symbol_yml_file, raw_pickle_file, pickle_dest_path):
    """
    Parameters
    ----------
    symbol_yml_file : str
        Path to a YAML file which contains recordings.
    raw_pickle_file : str
        Path to a pickle file which contains raw recordings.
    pickle_dest_path : str
        Path where the filtered dict gets serialized as a pickle file again.
    """
    metadata = get_metadata()
    symbol_ids = get_symbol_ids(symbol_yml_file, metadata)
    symbol_ids = transform_sids(symbol_ids)
    raw = load_raw(raw_pickle_file)
    filter_and_save(raw, symbol_ids, pickle_dest_path)


def get_symbol_ids(symbol_yml_file, metadata):
    """
    Get a list of ids which describe which class they get mapped to.

    Parameters
    ----------
    symbol_yml_file : string
        Path to a YAML file.
    metadata : dict
        Metainformation of symbols, like the id on write-math.com.
        Has keys 'symbols', 'tags', 'tags2symbols'.

    Returns
    -------
    list of dictionaries : Each dictionary represents one output class and has
        to have the keys 'id' (which is an id on write-math.com) and
        'mappings' (which is a list of ids on write-math.com). The mappings
        list should at least contain the id itself, but can contain more.

    Examples
    --------
    >>> get_symbol_ids('symbols.yml')
    [{'id': 42, 'mappings': [1, 42, 456, 1337]}, {'id': 2, 'mappings': [2]}]

    The yml file has to be of the structure

    ```
    - {latex: 'A'}
    - {latex: 'B'}
    - {latex: 'O',
       mappings: ['0', 'o']}
    - {latex: 'C'}
    - {latex: '::REJECT::',
       mappings: ['::ALL_FREE::']}
    - {latex: '::ARROW::',
       mappings: ['::TAG/arrow::'],
       exclude: ['\rightarrow']}
    ```
    """
    with open(symbol_yml_file, 'r') as stream:
        symbol_cfg = yaml.load(stream)
    symbol_ids = []
    symbol_ids_set = set()

    for symbol in symbol_cfg:
        if 'latex' not in symbol:
            logging.error("Key 'latex' not found for a symbol in %s (%s)",
                          symbol_yml_file,
                          symbol)
            sys.exit(-1)
        results = [el for el in metadata['symbols']
                   if el['formula_in_latex'] == symbol['latex']]
        if len(results) != 1:
            logging.warning("Found %i results for %s: %s",
                            len(results),
                            symbol['latex'],
                            results)
            if len(results) > 1:
                results = sorted(results, key=lambda n: n['id'])
            else:
                sys.exit(-1)
        mapping_ids = [results[0]['id']]
        if 'mappings' in symbol:
            for msymbol in symbol['mappings']:
                filtered = [el for el in metadata['symbols']
                            if el['formula_in_latex'] == msymbol['latex']]
                if len(filtered) != 1:
                    logging.error("Found %i results for %s: %s",
                                  len(filtered),
                                  msymbol,
                                  filtered)
                    if len(filtered) > 1:
                        filtered = natsorted(filtered, key=lambda n: n['id'])
                    else:
                        sys.exit(-1)
                mapping_ids.append(filtered[0]['id'])
        symbol_ids.append({'id': int(results[0]['id']),
                           'formula_in_latex': results[0]['formula_in_latex'],
                           'mappings': mapping_ids})
        for id_tmp in mapping_ids:
            if id_tmp not in symbol_ids_set:
                symbol_ids_set.add(id_tmp)
            else:
                for symbol_tmp in symbol_ids:
                    if id_tmp in symbol_tmp['mappings']:
                        break
                logging.error('Symbol id %s is already used: %s',
                              id_tmp,
                              symbol_tmp)
                sys.exit(-1)

    # print(metadata.keys())
    # for el in metadata:
    #    print(metadata[el][0].keys())
    # TODO: assert no double mappings
    # TODO: Support for
    # - ::ALL_FREE:: - meaning the rest of all ids which are not assigned to
    #                  any other class get assigned to this class
    # - ::TAG/arrow:: - meaning all ids of the tag arrow get assigned here
    # - exclude
    logging.info('%i base classes and %i write-math ids.',
                 len(symbol_ids),
                 len(symbol_ids_set))
    return symbol_ids


def transform_sids(symbol_ids):
    new_sids = {}
    for to_sid in symbol_ids:
        for from_sid in to_sid['mappings']:
            new_sids[int(from_sid)] = int(to_sid['id'])
    return new_sids


def get_metadata():
    """
    Get metadata of symbols, like their tags, id on write-math.com, LaTeX
    command and unicode code point.

    Returns
    -------
    dict
    """
    misc_path = pkg_resources.resource_filename('hwrt', 'misc/')
    wm_symbols = os.path.join(misc_path, 'wm_symbols.csv')
    wm_tags = os.path.join(misc_path, 'wm_tags.csv')
    wm_tags2symbols = os.path.join(misc_path, 'wm_tags2symbols.csv')
    return {'symbols': read_csv(wm_symbols),
            'tags': read_csv(wm_tags),
            'tags2symbols': read_csv(wm_tags2symbols)}


def read_csv(filepath):
    """
    Read a CSV into a list of dictionarys. The first line of the CSV determines
    the keys of the dictionary.

    Parameters
    ----------
    filepath : string

    Returns
    -------
    list of dictionaries
    """
    symbols = []
    with open(filepath, 'rb') as csvfile:
        spamreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in spamreader:
            symbols.append(row)
    return symbols


def load_raw(raw_pickle_file):
    """
    Load a pickle file of raw recordings.

    Parameters
    ----------
    raw_pickle_file : str
        Path to a pickle file which contains raw recordings.

    Returns
    -------
    dict
        The loaded pickle file.
    """
    with open(raw_pickle_file, 'rb') as f:
        raw = pickle.load(f)
    logging.info("Loaded %i recordings.", len(raw['handwriting_datasets']))
    return raw


def filter_and_save(raw, symbol_ids, destination_path):
    """
    Parameters
    ----------
    raw : dict
        with key 'handwriting_datasets'
    symbol_ids : dict
        Maps LaTeX to write-math.com id
    destination_path : str
        Path where the filtered dict 'raw' will be saved
    """
    logging.info('Start filtering...')
    new_hw_ds = []
    for el in raw['handwriting_datasets']:
        if el['formula_id'] in symbol_ids:
            el['formula_id'] = symbol_ids[el['formula_id']]
            el['handwriting'].formula_id = symbol_ids[el['formula_id']]
            new_hw_ds.append(el)
    raw['handwriting_datasets'] = new_hw_ds

    # pickle
    logging.info('Start dumping %i recordings...', len(new_hw_ds))
    pickle.dump(raw, open(destination_path, "wb"), 2)


def get_parser():
    """Return the parser object for this script."""
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-s", "--symbol",
                        dest="symbol_filename",
                        type=lambda x: utils.is_valid_file(parser, x),
                        required=True,
                        help="symbol yml file",
                        metavar="FILE")
    parser.add_argument("-r", "--raw",
                        dest="raw_filename",
                        type=lambda x: utils.is_valid_file(parser, x),
                        required=True,
                        help="raw pickle file",
                        metavar="FILE")
    parser.add_argument("-d", "--dest",
                        dest="pickle_dest_path",
                        required=True,
                        help="pickle destination file",
                        metavar="FILE")
    return parser


if __name__ == '__main__':
    args = get_parser().parse_args()
    main(args.symbol_filename, args.raw_filename, args.pickle_dest_path)
