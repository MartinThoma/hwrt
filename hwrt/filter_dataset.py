#!/usr/bin/env python

"""
Given a dataset and a vocabulary file, filter the recordings which are desired.
"""
# This has to work with preprocess_dataset.py

# Core Library modules
import csv
import logging
import os
import pickle
import sys
from typing import Any, Dict, List, Sequence, Set

# Third party modules
import pkg_resources
import yaml
from natsort import natsorted

logger = logging.getLogger(__name__)


def main(symbol_yml_file: str, raw_pickle_file: str, pickle_dest_path: str):
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


def get_symbol_ids(
    symbol_yml_file: str, metadata: Dict[Any, Any]
) -> List[Dict[str, Any]]:
    r"""
    Get a list of ids which describe which class they get mapped to.

    Parameters
    ----------
    symbol_yml_file : str
        Path to a YAML file.
    metadata : Dict[Any, Any]
        Metainformation of symbols, like the id on write-math.com.
        Has keys 'symbols', 'tags', 'tags2symbols'.

    Returns
    -------
    symbol_ids : List[Dict[str, Any]]
        Each dictionary represents one output class and has
        to have the keys 'id' (which is an id on write-math.com) and
        'mappings' (which is a list of ids on write-math.com). The mappings
        list should at least contain the id itself, but can contain more.

    Examples
    --------
    >>> from hwrt.utils import get_symbols_filepath
    >>> metadata = {"symbols": [{"formula_in_latex": r"\alpha", "id": 42},
    ...                         {"formula_in_latex": r"\beta", "id": 1337}]}
    >>> out = get_symbol_ids(get_symbols_filepath(testing=True), metadata=metadata)
    >>> len(out)
    2
    >>> out[0]
    {'id': 42, 'formula_in_latex': '\\alpha', 'mappings': [42]}
    >>> out[1]
    {'id': 1337, 'formula_in_latex': '\\beta', 'mappings': [1337]}

    The YAML file has to be of the structure

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
    with open(symbol_yml_file) as stream:
        symbol_cfg = yaml.safe_load(stream)
    symbol_ids = []
    symbol_ids_set: Set[str] = set()

    for symbol in symbol_cfg:
        if "latex" not in symbol:
            logger.error(
                "Key 'latex' not found for a symbol in %s (%s)", symbol_yml_file, symbol
            )
            sys.exit(-1)
        results = [
            el
            for el in metadata["symbols"]
            if el["formula_in_latex"] == symbol["latex"]
        ]
        if len(results) != 1:
            logger.warning(
                "Found %i results for %s: %s", len(results), symbol["latex"], results
            )
            if len(results) > 1:
                results = sorted(results, key=lambda n: n["id"])
            else:
                sys.exit(-1)
        mapping_ids = [results[0]["id"]]
        if "mappings" in symbol:
            for msymbol in symbol["mappings"]:
                filtered = [
                    el
                    for el in metadata["symbols"]
                    if el["formula_in_latex"] == msymbol["latex"]
                ]
                if len(filtered) != 1:
                    logger.error(
                        "Found %i results for %s: %s", len(filtered), msymbol, filtered
                    )
                    if len(filtered) > 1:
                        filtered = natsorted(filtered, key=lambda n: n["id"])
                    else:
                        sys.exit(-1)
                mapping_ids.append(filtered[0]["id"])
        symbol_ids.append(
            {
                "id": int(results[0]["id"]),
                "formula_in_latex": results[0]["formula_in_latex"],
                "mappings": mapping_ids,
            }
        )
        for id_tmp in mapping_ids:
            if id_tmp not in symbol_ids_set:
                symbol_ids_set.add(id_tmp)
            else:
                for symbol_tmp in symbol_ids:
                    if id_tmp in symbol_tmp["mappings"]:
                        break
                logger.error("Symbol id %s is already used: %s", id_tmp, symbol_tmp)
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
    logger.info(
        "%i base classes and %i write-math ids.", len(symbol_ids), len(symbol_ids_set)
    )
    return symbol_ids


def transform_sids(symbol_ids):
    new_sids = {}
    for to_sid in symbol_ids:
        for from_sid in to_sid["mappings"]:
            new_sids[int(from_sid)] = int(to_sid["id"])
    return new_sids


def get_metadata() -> Dict[str, Any]:
    """
    Get metadata of symbols, like their tags, id on write-math.com, LaTeX
    command and unicode code point.
    """
    misc_path = pkg_resources.resource_filename("hwrt", "misc/")
    wm_symbols = os.path.join(misc_path, "wm_symbols.csv")
    wm_tags = os.path.join(misc_path, "wm_tags.csv")
    wm_tags2symbols = os.path.join(misc_path, "wm_tags2symbols.csv")
    return {
        "symbols": read_csv(wm_symbols),
        "tags": read_csv(wm_tags),
        "tags2symbols": read_csv(wm_tags2symbols),
    }


def read_csv(filepath: str) -> Sequence[Dict[Any, Any]]:
    """
    Read a CSV into a list of dictionarys. The first line of the CSV determines
    the keys of the dictionary.

    Parameters
    ----------
    filepath : str

    Returns
    -------
    symbols : List[Dict]
    """
    symbols = []
    with open(filepath) as csvfile:
        spamreader = csv.DictReader(csvfile, delimiter=",", quotechar='"')
        for row in spamreader:
            symbols.append(row)
    return symbols


def load_raw(raw_pickle_file: str) -> Dict[Any, Any]:
    """
    Load a pickle file of raw recordings.

    Parameters
    ----------
    raw_pickle_file : str
        Path to a pickle file which contains raw recordings.

    Returns
    -------
    raw : Dict[Any, Any]
        The loaded pickle file.
    """
    with open(raw_pickle_file, "rb") as f:
        raw = pickle.load(f)
    logger.info("Loaded %i recordings.", len(raw["handwriting_datasets"]))
    return raw


def filter_and_save(
    raw: Dict[Any, Any], symbol_ids: List[Dict[str, Any]], destination_path: str
):
    """
    Parameters
    ----------
    raw : Dict[Any, Any]
        with key 'handwriting_datasets'
    symbol_ids : Dict[str, Any]
        Maps LaTeX to write-math.com id
    destination_path : str
        Path where the filtered dict 'raw' will be saved
    """
    logger.info("Start filtering...")
    new_hw_ds = []
    for el in raw["handwriting_datasets"]:
        if el["formula_id"] in symbol_ids:
            el["formula_id"] = symbol_ids[el["formula_id"]]
            el["handwriting"].formula_id = symbol_ids[el["formula_id"]]
            new_hw_ds.append(el)
    raw["handwriting_datasets"] = new_hw_ds

    # pickle
    logger.info("Start dumping %i recordings...", len(new_hw_ds))
    pickle.dump(raw, open(destination_path, "wb"), 2)
