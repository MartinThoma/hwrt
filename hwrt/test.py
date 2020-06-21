#!/usr/bin/env python

"""Get the error of a model. This tool supports multiple error measures."""

# Core Library modules
import csv
import itertools
import logging
import os
import subprocess
import sys
import tempfile
import time
from collections import Callable, OrderedDict

# Third party modules
import pkg_resources
import yaml

# First party modules
import hwrt.utils as utils

logger = logging.getLogger(__name__)


class DefaultOrderedDict(OrderedDict):
    # Source: http://stackoverflow.com/a/6190500/562769
    def __init__(self, default_factory=None, *a, **kw):
        if default_factory is not None and not isinstance(default_factory, Callable):
            raise TypeError("first argument must be callable")
        OrderedDict.__init__(self, *a, **kw)
        self.default_factory = default_factory

    def __getitem__(self, key):
        try:
            return OrderedDict.__getitem__(self, key)
        except KeyError:
            return self.__missing__(key)

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = value = self.default_factory()
        return value

    def __reduce__(self):
        if self.default_factory is None:
            args = tuple()
        else:
            args = (self.default_factory,)
        return type(self), args, None, None, list(self.items())

    def copy(self):
        return self.__copy__()

    def __copy__(self):
        return type(self)(self.default_factory, self)

    def __deepcopy__(self, memo):
        import copy

        return type(self)(self.default_factory, copy.deepcopy(list(self.items())))

    def __repr__(self):
        return "OrderedDefaultDict({}, {})".format(
            self.default_factory, OrderedDict.__repr__(self),
        )


def get_test_results(model_folder, basename, test_file):
    model_src = utils.get_latest_model(model_folder, basename)
    if model_src is None:
        logger.error(f"No model with basename '{basename}' found in '{model_folder}'.")
    else:
        _, model_use = tempfile.mkstemp(suffix=".json", text=True)
        utils.create_adjusted_model_for_percentages(model_src, model_use)

        # Start evaluation
        project_root = utils.get_project_root()
        time_prefix = time.strftime("%Y-%m-%d-%H-%M")
        logger.info(f"Evaluate '{model_src}' with '{test_file}'...")
        logfile = os.path.join(
            project_root, "logs/%s-error-evaluation.log" % time_prefix
        )
        logger.info(f"Write log to {logfile}...")
        with open(logfile, "w") as log, open(model_use) as model_src_p:
            p = subprocess.Popen(
                [
                    utils.get_nntoolkit(),
                    "run",
                    "--batch-size",
                    "1",
                    "-f%0.4f",
                    test_file,
                ],
                stdin=model_src_p,
                stdout=log,
            )
            ret = p.wait()
            if ret != 0:
                logger.error(f"nntoolkit finished with ret code {ret}")
                sys.exit(-1)
        os.remove(model_use)
        return logfile


def make_all(tuplelist):
    t = []
    for confusiongroup in tuplelist:
        for x, y in itertools.permutations(confusiongroup, 2):
            t.append((x, y))
    return t


def create_report(true_data, eval_data, index2latex, n, merge=True):
    r"""
    Parameters
    ----------
    true_data : list
        Labels
    eval_data : list
        Predicted labels
    index2latex : dict
        Maps the output neurons index to LaTeX
    n : TODO?
    merge : bool
        If set to True, some symbols like \sum and \Sigma will not be count as
        errors when confused.
    """
    # Gather data
    correct = []
    wrong = []
    # Get MER classes
    merge_cfg_path = pkg_resources.resource_filename(__name__, "misc/")
    merge_cfg_file = os.path.join(merge_cfg_path, "merge.yml")
    merge_data = yaml.safe_load(open(merge_cfg_file))
    # Make classes
    confusing = make_all(merge_data)
    if not merge:
        confusing = []

    # Get false/true negative/positive for each symbol
    statistical = {}
    possible_keys = []

    assert len(true_data) > 0, "true_data was empty"
    assert len(true_data) == len(eval_data), "len(true_data)=%i, len(eval_data)=%i" % (
        len(true_data),
        len(eval_data),
    )
    for known, evaluated in zip(true_data, eval_data):
        evaluated_t1 = list(evaluated.keys())[0]
        if known["index"] not in statistical:
            statistical[known["index"]] = {
                "FP": 0,
                "TP": 0,
                "FN": 0,
                "TN": 0,
                "latex": index2latex[known["index"]],
            }
            possible_keys.append(known["index"])
        for key in list(evaluated.keys()):
            if key not in statistical:
                if key not in index2latex:
                    logger.error(
                        f"Key '{key}' is not in index2latex. Did you "
                        "probaly define a too small number of "
                        "outputnodes?"
                    )
                    logger.error(f"index2latex.keys(): {index2latex.keys()}")
                    sys.exit(-1)
                statistical[key] = {
                    "FP": 0,
                    "TP": 0,
                    "FN": 0,
                    "TN": 0,
                    "latex": index2latex[key],
                }
                possible_keys.append(key)
        if known["index"] in list(evaluated.keys())[:n]:
            statistical[known["index"]]["TP"] += 1
            correct.append(known)
            for key in possible_keys:
                if key != known["index"]:
                    statistical[key]["TN"] += 1
        elif (index2latex[known["index"]], index2latex[evaluated_t1]) in confusing:
            # Some confusions are ok!
            statistical[known["index"]]["TP"] += 1
            correct.append(known)
            for key in possible_keys:
                if key != known["index"]:
                    statistical[key]["TN"] += 1
        else:
            for key in possible_keys:
                if key != known["index"]:
                    if key not in list(evaluated.keys())[:n]:
                        statistical[key]["TN"] += 1
                    else:
                        statistical[key]["FP"] += 1
                else:
                    statistical[key]["FN"] += 1
            formula_id = index2latex[evaluated_t1]
            known["confused"] = formula_id  # That's an index!
            wrong.append(known)
    classification_error = len(wrong) / float(len(wrong) + len(correct))
    logger.info(
        f"Classification error (n={n}, MER={merge}): "
        f"{classification_error:0.4f} ({len(wrong)} of {len(eval_data)} wrong)",
    )

    # Get the data
    errors_by_correct_classification = DefaultOrderedDict(list)
    errors_by_wrong_classification = DefaultOrderedDict(list)
    for el in wrong:
        errors_by_correct_classification[el["latex"]].append(el)
        errors_by_wrong_classification[el["confused"]].append(el)

    # Sort errors_by_correct_classification
    tmp = sorted(
        iter(errors_by_correct_classification.items()),
        key=lambda n: len(n[1]),
        reverse=True,
    )
    errors_by_correct_classification = OrderedDict(tmp)
    for key in errors_by_correct_classification:
        tmp = sorted(errors_by_correct_classification[key], key=lambda n: n["confused"])
        errors_by_correct_classification[key] = tmp
    # Sort errors_by_wrong_classification
    tmp = sorted(
        iter(errors_by_wrong_classification.items()),
        key=lambda n: len(n[1]),
        reverse=True,
    )
    errors_by_wrong_classification = OrderedDict(tmp)
    for key in errors_by_wrong_classification:
        tmp = sorted(errors_by_wrong_classification[key], key=lambda n: n["latex"])
        errors_by_wrong_classification[key] = tmp

    # Get the tempalte
    project_root = utils.get_project_root()
    template_path = pkg_resources.resource_filename("hwrt", "templates/")
    template = os.path.join(template_path, "classification-error-report.html")
    with open(template) as f:
        template = f.read()

    # Find right place for report file
    time_prefix = time.strftime("%Y-%m-%d-%H-%M")
    directory = os.path.join(project_root, "reports")
    if not os.path.exists(directory):
        os.makedirs(directory)
    target = os.path.join(
        project_root, ("reports/" "%s-classification-error-report.html") % time_prefix
    )
    # Fill the template
    from jinja2 import FileSystemLoader
    from jinja2.environment import Environment

    env = Environment()
    env.loader = FileSystemLoader(template_path)
    t = env.get_template("classification-error-report.html")
    rendered = t.render(
        wrong=wrong,
        correct=correct,
        classification_error=classification_error,
        errors_by_correct_classification=errors_by_correct_classification,
        errors_by_wrong_classification=errors_by_wrong_classification,
        statistical=statistical,
    )
    with open(target, "w") as f:
        f.write(rendered)


def analyze_results(
    translation_csv, what_evaluated_file, evaluation_file, n, merge=True
):
    r"""
    Parameters
    ----------
    translation_csv : string
        Path to a CSV file which translates the output neuron into semantics.
    what_evaluated_file : string
        Path to a CSV file which translates testing data to LaTeX labels
        (and more?)
    evaluation_file : string
        Path to a file which has the test data.
    n : ?
    merge : bool
        If set to True, some symbols like \sum and \Sigma will not be count as
        errors when confused.
    """
    index2latex = {}
    with open(translation_csv) as csvfile:
        spamreader = csv.DictReader(csvfile, delimiter=",", quotechar='"')
        for row in spamreader:
            index2latex[int(row["index"])] = row["latex"]
    with open(evaluation_file) as f:
        eval_data = f.readlines()  # Has no heading

    # Get probability array (index is class)
    for i in range(len(eval_data)):
        eval_data[i] = eval_data[i].strip()
        splitted = eval_data[i].split(" ")
        if len(splitted) == 0:
            continue  # Skip empty lines
        eval_data[i] = list(map(float, splitted))

        # index -> probability dictionary
        d = OrderedDict()
        for index, prob in enumerate(eval_data[i]):
            d[index] = prob
        # Sort descending by probability
        d = OrderedDict(sorted(iter(d.items()), key=lambda n: n[1], reverse=True))
        eval_data[i] = d

    true_data = []
    with open(what_evaluated_file) as csvfile:
        spamreader = csv.DictReader(csvfile, delimiter=",", quotechar='"')
        for row in spamreader:
            row["index"] = int(row["index"])
            true_data.append(row)

    create_report(true_data, eval_data, index2latex, n, merge)


def main(model_folder, aset="test", n=3, merge=True):
    """Main part of the test script."""
    project_root = utils.get_project_root()

    if aset == "test":
        key_model, key_file = "testing", "testdata"
    elif aset == "valid":
        key_model, key_file = "validating", "validdata"
    else:
        key_model, key_file = "training", "traindata"

    # Get model description
    model_description_file = os.path.join(model_folder, "info.yml")
    # Read the model description file
    with open(model_description_file) as ymlfile:
        model_description = yaml.safe_load(ymlfile)

    # Get the data paths (hdf5)
    project_root = utils.get_project_root()
    data = {}
    data["training"] = os.path.join(
        project_root, model_description["data-source"], "traindata.hdf5"
    )
    data["testing"] = os.path.join(
        project_root, model_description["data-source"], "testdata.hdf5"
    )
    data["validating"] = os.path.join(
        project_root, model_description["data-source"], "validdata.hdf5"
    )

    test_data_path = os.path.join(model_folder, data[key_model])
    evaluation_file = get_test_results(model_folder, "model", test_data_path)
    translation_csv = os.path.join(
        project_root, model_description["data-source"], "index2formula_id.csv"
    )
    what_evaluated_file = os.path.join(
        project_root, model_description["data-source"], "translation-%s.csv" % key_file
    )
    analyze_results(translation_csv, what_evaluated_file, evaluation_file, n, merge)
