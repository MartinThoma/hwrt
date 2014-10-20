#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Get the error of a model. This tool supports multiple error measures."""

import logging
import sys
import os
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)
import subprocess
import time
import yaml
import csv
import itertools
import shutil
from collections import OrderedDict, Callable
import pkg_resources
# mine
import hwrt.utils as utils


class DefaultOrderedDict(OrderedDict):
    # Source: http://stackoverflow.com/a/6190500/562769
    def __init__(self, default_factory=None, *a, **kw):
        if (default_factory is not None and
           not isinstance(default_factory, Callable)):
            raise TypeError('first argument must be callable')
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
            args = self.default_factory,
        return type(self), args, None, None, self.items()

    def copy(self):
        return self.__copy__()

    def __copy__(self):
        return type(self)(self.default_factory, self)

    def __deepcopy__(self, memo):
        import copy
        return type(self)(self.default_factory,
                          copy.deepcopy(self.items()))

    def __repr__(self):
        return 'OrderedDefaultDict(%s, %s)' % (self.default_factory,
                                               OrderedDict.__repr__(self))


def get_test_results(model_folder, basename, test_file):
    model_src = utils.get_latest_model(model_folder, basename)
    if model_src is None:
        logging.error("No model with basename '%s' found in '%s'.",
                      basename,
                      model_folder)
    else:
        # Copy model file
        model_use = "tmp.json"  # TODO write elsewhere in a temporary folder
        shutil.copyfile(model_src, model_use)
        # Adjust model file
        with open(model_src) as f:
            content = f.read()
        content = content.replace("logreg", "sigmoid")
        with open(model_use, "w") as f:
            f.write(content)

        # Start evaluation
        PROJECT_ROOT = utils.get_project_root()
        time_prefix = time.strftime("%Y-%m-%d-%H-%M")
        logging.info("Evaluate '%s' with '%s'...", model_src, test_file)
        logfile = os.path.join(PROJECT_ROOT,
                               "logs/%s-error-evaluation.log" %
                               time_prefix)
        with open(logfile, "w") as log, open(model_use, "r") as model_src_p:
            p = subprocess.Popen(['nntoolkit', 'run',
                                  '--batch-size', '1', '-f%0.4f', test_file],
                                 stdin=model_src_p,
                                 stdout=log)
            ret = p.wait()
            if ret != 0:
                logging.error("nntoolkit finished with ret code %s", str(ret))
                sys.exit()
        return logfile


def make_all(tuplelist):
    t = []
    for confusiongroup in tuplelist:
        for x, y in itertools.permutations(confusiongroup, 2):
            t.append((x, y))
    return t


def create_report(true_data, eval_data, index2latex, n, merge=True):
    # Gather data
    correct = []
    wrong = []
    confusing = [('\sum', '\Sigma'),
                 ('\prod', '\Pi', '\sqcap'),
                 ('\coprod', '\\amalg', '\\sqcup'),
                 ('\perp', '\\bot'),
                 ('\models', '\\vDash'),
                 ('|', '\mid'),
                 ('\Delta', '\\triangle', '\\vartriangle'),
                 ('\|', '\parallel'),
                 ('\ohm', '\Omega'),
                 ('\setminus', '\\backslash'),
                 ('\checked', '\checkmark'),
                 ('\&', '\with'),
                 ('\#', '\sharp'),
                 ('\S', '\mathsection'),
                 ('\\nabla', '\\triangledown'),
                 ('\lhd', '\\triangleleft', '\\vartriangleleft'),
                 ('\\oiint', '\\varoiint'),
                 ('\mathbb{R}', '\mathds{R}'),
                 ('\mathbb{Q}', '\mathds{Q}'),
                 ('\mathbb{Z}', '\mathds{Z}'),
                 ('\mathcal{A}', '\mathscr{A}'),
                 ('\mathcal{D}', '\mathscr{D}'),
                 ('\mathcal{N}', '\mathscr{N}'),
                 ('\mathcal{R}', '\mathscr{R}'),
                 ('\propto', '\\varpropto')]
    understandable = [('\\alpha', '\propto', '\\varpropto', '\ltimes'),
                      ('0', 'O', 'o', '\circ', '\degree', '\\fullmoon', '\mathcal{O}'),
                      ('\epsilon', '\\varepsilon', '\in', '\mathcal{E}'),
                      ('\Lambda', '\wedge'),
                      ('\emptyset', '\O', '\o', '\diameter', '\\varnothing'),
                      ('\\rightarrow', '\longrightarrow', '\shortrightarrow'),
                      ('\Rightarrow', '\Longrightarrow'),
                      ('\Leftrightarrow', '\Longleftrightarrow'),
                      ('\mapsto', '\longmapsto'),
                      ('\mathbb{1}', '\mathds{1}'),
                      ('\mathscr{L}', '\mathcal{L}'),
                      ('\\mathbb{Q}', '\\mathds{Q}'),
                      ('\\mathbb{Z}', '\\mathds{Z}', '\\mathcal{Z}'),
                      ('\geq', '\geqslant', '\succeq'),
                      ('\leq', '\leqslant'),
                      ('\Pi', '\pi', '\prod'),
                      ('\psi', '\Psi'),
                      ('\phi', '\Phi', '\emptyset'),
                      ('\\rho', '\\varrho'),
                      ('\\theta', '\Theta'),
                      ('\odot', '\\astrosun'),
                      ('\cdot', '\\bullet'),
                      ('\\beta', '\ss'),
                      ('\male', '\mars'),
                      ('\\female', '\\venus'),
                      ('\Bowtie', '\\bowtie'),
                      ('\diamond', '\diamondsuit', '\lozenge'),
                      ('\dots', '\dotsc'),
                      ('\mathcal{T}', '\\tau'),
                      ('\mathcal{C}', 'C'),
                      ('x', '\\times', 'X', '\\chi', '\\mathcal{X}')]
    confusing = make_all(confusing)
    if not merge:
        confusing = []
    if False:
        confusing += make_all(understandable)
    for known, evaluated in zip(true_data, eval_data):
        evaluated_t1 = evaluated.keys()[0]
        if known['index'] in evaluated.keys()[:n]:
            correct.append(known)
        elif (index2latex[known['index']],
              index2latex[evaluated_t1]) in confusing:
            # Some confusions are ok!
            correct.append(known)
        else:
            formula_id = index2latex[evaluated_t1]
            known['confused'] = formula_id  # That's an index!
            wrong.append(known)
    classification_error = (len(wrong) / float(len(wrong) + len(correct)))
    logging.info("Classification error: %0.4f (%i wrong)" %
                 (classification_error, len(wrong)))

    # Get the data
    errors_by_correct_classification = DefaultOrderedDict(list)
    errors_by_wrong_classification = DefaultOrderedDict(list)
    for el in wrong:
        errors_by_correct_classification[el['latex']].append(el)
        errors_by_wrong_classification[el['confused']].append(el)

    # Sort errors_by_correct_classification
    errors_by_correct_classification = OrderedDict(sorted(errors_by_correct_classification.iteritems(),
                                                   key=lambda n: len(n[1]),
                                                   reverse=True))
    for key in errors_by_correct_classification:
        errors_by_correct_classification[key] = sorted(errors_by_correct_classification[key],
                                                       key=lambda n: n['confused'])
    # Sort errors_by_wrong_classification
    errors_by_wrong_classification = OrderedDict(sorted(errors_by_wrong_classification.iteritems(),
                                                 key=lambda n: len(n[1]),
                                                 reverse=True))
    for key in errors_by_wrong_classification:
        errors_by_wrong_classification[key] = sorted(errors_by_wrong_classification[key],
                                                     key=lambda n: n['latex'])

    # Get the tempalte
    PROJECT_ROOT = utils.get_project_root()
    template = os.path.join(PROJECT_ROOT,
                            "tools/templates/classification-error-report.html")
    with open(template) as f:
        template = f.read()

    # Find right place for report file
    time_prefix = time.strftime("%Y-%m-%d-%H-%M")
    target = os.path.join(PROJECT_ROOT,
                          ("reports/"
                           "%s-classification-error-report.html") %
                          time_prefix)
    # Fill the template
    from jinja2 import FileSystemLoader
    from jinja2.environment import Environment
    env = Environment()
    template_path = pkg_resources.resource_filename('hwrt', 'templates/')
    env.loader = FileSystemLoader(template_path)
    t = env.get_template('classification-error-report.html')
    rendered = t.render(wrong=wrong, correct=correct,
                        classification_error=classification_error,
                        errors_by_correct_classification=
                        errors_by_correct_classification,
                        errors_by_wrong_classification=
                        errors_by_wrong_classification)
    with open(target, "w") as f:
        f.write(rendered)


def analyze_results(translation_csv, what_evaluated_file, evaluation_file, n,
                    merge=True):
    index2latex = {}
    with open(translation_csv) as csvfile:
        spamreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in spamreader:
            index2latex[int(row['index'])] = row['latex']
    with open(evaluation_file) as f:
        eval_data = f.readlines()  # Has no heading

    # Get probability array (index is class)
    for i in range(len(eval_data)):
        eval_data[i] = eval_data[i].strip()
        splitted = eval_data[i].split(" ")
        if len(splitted) == 0:
            continue  # Skip empty lines
        eval_data[i] = map(float, splitted)

        # index -> probability dictionary
        d = OrderedDict()
        for index, prob in enumerate(eval_data[i]):
            d[index] = prob
        # Sort descending by probability
        d = OrderedDict(sorted(d.iteritems(),
                        key=lambda n: n[1],
                        reverse=True))
        eval_data[i] = d

    true_data = []
    with open(what_evaluated_file) as csvfile:
        spamreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in spamreader:
            row['index'] = int(row['index'])
            true_data.append(row)

    create_report(true_data, eval_data, index2latex, n, merge)


def main(model_folder, aset='test', n=3, merge=True):
    PROJECT_ROOT = utils.get_project_root()

    if aset == 'test':
        key_model, key_file = 'testing', 'testdata'
    elif aset == 'valid':
        key_model, key_file = 'validating', 'validdata'
    else:
        key_model, key_file = 'training', 'traindata'

    # Get model description
    model_description_file = os.path.join(model_folder, "info.yml")
    # Read the model description file
    with open(model_description_file, 'r') as ymlfile:
        model_description = yaml.load(ymlfile)

    # Get the data paths (pfiles)
    PROJECT_ROOT = utils.get_project_root()
    data = {}
    data['training'] = os.path.join(PROJECT_ROOT,
                                    model_description["data-source"],
                                    "traindata.pfile")
    data['testing'] = os.path.join(PROJECT_ROOT,
                                   model_description["data-source"],
                                   "testdata.pfile")
    data['validating'] = os.path.join(PROJECT_ROOT,
                                      model_description["data-source"],
                                      "validdata.pfile")

    test_data_path = os.path.join(model_folder, data[key_model])
    evaluation_file = get_test_results(model_folder,
                                       "model",
                                       test_data_path)
    translation_csv = os.path.join(PROJECT_ROOT,
                                   model_description["data-source"],
                                   "index2formula_id.csv")
    what_evaluated_file = os.path.join(PROJECT_ROOT,
                                       model_description["data-source"],
                                       "translation-%s.csv" % key_file)
    analyze_results(translation_csv, what_evaluated_file, evaluation_file, n,
                    merge)


def is_valid_file(parser, arg):
    """Check if arg is a valid file that already exists on the file
       system.
    """
    arg = os.path.abspath(arg)
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg


def get_parser():
    PROJECT_ROOT = utils.get_project_root()

    # Get latest model folder
    models_folder = os.path.join(PROJECT_ROOT, "models")
    latest_model = utils.get_latest_folder(models_folder)

    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-m", "--model",
                        dest="model",
                        help="where is the model folder (with the info.yml)?",
                        metavar="FOLDER",
                        type=lambda x: utils.is_valid_folder(parser, x),
                        default=latest_model)
    parser.add_argument("-s", "--set",
                        dest="aset",
                        choices=['test', 'train', 'valid'],
                        help="which set should get analyzed?",
                        default='test')
    parser.add_argument("-n",
                        dest="n", default=3, type=int,
                        help="Top-N error")
    parser.add_argument("--merge",
                        action="store_true", dest="merge", default=False,
                        help="merge problem classes that are easy to confuse")
    return parser


if __name__ == "__main__":
    args = get_parser().parse_args()
    main(args.model, args.aset, args.n, args.merge)
