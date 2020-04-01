#!/usr/bin/env python

"""Merge two raw data pickle files."""

# Core Library modules
import pickle
from typing import Dict

# Third party modules
import click


def main(dataset1: str, dataset2: str, target: str):
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
    with open(target, "wb") as f:
        pickle.dump(merged, f, protocol=pickle.HIGHEST_PROTOCOL)


def read_raw(data_path: str):
    """
    Parameters
    ----------
    data_path : str
    """
    with open(data_path, "rb") as f:
        data = pickle.load(f)
    return data


def merge(d1: Dict, d2: Dict) -> Dict:
    """Merge two raw datasets into one.

    Parameters
    ----------
    d1 : Dict
    d2 : Dict

    Returns
    -------
    Dict
    """
    if d1["formula_id2latex"] is None:
        formula_id2latex = {}
    else:
        formula_id2latex = d1["formula_id2latex"].copy()
    formula_id2latex.update(d2["formula_id2latex"])
    handwriting_datasets = d1["handwriting_datasets"]
    for dataset in d2["handwriting_datasets"]:
        handwriting_datasets.append(dataset)
    return {
        "formula_id2latex": formula_id2latex,
        "handwriting_datasets": handwriting_datasets,
    }


@click.command()
@click.option(
    "-d1",
    type=click.Path(dir_okay=False, file_okay=True, exists=True),
    help="dataset 1",
    required=True,
)
@click.option(
    "-d2",
    type=click.Path(dir_okay=False, file_okay=True, exists=True),
    help="dataset 2",
    required=True,
)
@click.option(
    "-t",
    "--target",
    type=click.Path(dir_okay=False, file_okay=True, exists=False),
    required=True,
)
def entry_point(d1, d2, target):
    main(d1, d2, target)


if __name__ == "__main__":
    entry_point()
