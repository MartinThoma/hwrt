#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the utility functions."""

import nose
import mock
import os
import argparse
import pkg_resources
import json

# hwrt modules
import hwrt
import hwrt.utils as utils


# Tests
def execution_test():
    """Test if the functions execute at all."""
    utils.get_project_root()
    utils.get_latest_model(".", "model")
    utils.get_latest_working_model(".")
    utils.get_latest_successful_run(".")
    nose.tools.assert_equal(utils.get_readable_time(123), "123ms")
    nose.tools.assert_equal(utils.get_readable_time(1000*30),
                            "30s 0ms")
    nose.tools.assert_equal(utils.get_readable_time(1000*60),
                            "1 minutes 0s 0ms")
    nose.tools.assert_equal(utils.get_readable_time(1000*60*60),
                            "1h, 0 minutes 0s 0ms")
    nose.tools.assert_equal(utils.get_readable_time(2*1000*60*60),
                            "2h, 0 minutes 0s 0ms")
    nose.tools.assert_equal(utils.get_readable_time(25*1000*60*60+3),
                            "25h, 0 minutes 0s 3ms")
    utils.print_status(3, 1, 123)
    utils.get_nntoolkit()
    utils.get_database_config_file()
    utils.get_database_configuration()
    nose.tools.assert_equal(utils.sizeof_fmt(1), "1.0 bytes")
    nose.tools.assert_equal(utils.sizeof_fmt(1111), "1.1 KB")


def parser_test():
    """Check the parser."""
    from argparse import ArgumentParser
    parser = ArgumentParser()
    home = os.path.expanduser("~")
    rcfile = os.path.join(home, ".hwrtrc")
    parser.add_argument("-m", "--model",
                        dest="model",
                        type=lambda x: utils.is_valid_folder(parser, x))
    parser.parse_args(['-m', home])

    parser = ArgumentParser()
    parser.add_argument("-m", "--model",
                        dest="model",
                        type=lambda x: utils.is_valid_file(parser, x))
    parser.parse_args(['-m', rcfile])


def get_class_test():
    """The get_class function returns a class for feature and preprocessing
       algorithms.
    """
    utils.get_class('ScaleAndShift', 'preprocessing', hwrt.preprocessing)
    utils.get_class('BongaBonga', 'preprocessing', hwrt.preprocessing)


def query_yes_no_test():
    """This function is used to get a binary decision by the user.
       Sadly, there are two different ways to use it due to Python 2 / 3.
    """
    try:
        import __builtin__
        builtins_str = "__builtin__.raw_input"
    except ImportError:
        builtins_str = "builtins.input"
    with mock.patch('%s' % builtins_str, return_value='y'):
        nose.tools.assert_equal(utils.query_yes_no("bla"), True)
        nose.tools.assert_equal(utils.query_yes_no("bla", None), True)
        nose.tools.assert_equal(utils.query_yes_no("bla", "yes"), True)
        nose.tools.assert_equal(utils.query_yes_no("bla", "no"), True)
    with mock.patch('%s' % builtins_str, return_value=''):
        nose.tools.assert_equal(utils.query_yes_no("bla", 'yes'), True)
        nose.tools.assert_equal(utils.query_yes_no("bla", 'no'), False)


def input_string_test():
    """Another Python 2/3 input hack."""
    try:
        import __builtin__
        with mock.patch('__builtin__.raw_input', return_value='y'):
            nose.tools.assert_equal(utils.input_string("bla"), "y")
    except ImportError:
        with mock.patch('builtins.input', return_value='y'):
            nose.tools.assert_equal(utils.input_string("bla"), "y")


def input_int_default_test():
    """Another Python 2/3 input hack."""
    try:
        import __builtin__
        builtins_str = "__builtin__.raw_input"
    except ImportError:
        builtins_str = "builtins.input"
    with mock.patch('%s' % builtins_str, return_value='yes'):
        nose.tools.assert_equal(utils.input_int_default("bla"), 0)
        nose.tools.assert_equal(utils.input_int_default("bla", 42), 42)
    with mock.patch('%s' % builtins_str, return_value=1337):
        nose.tools.assert_equal(utils.input_int_default("bla"), 1337)
        nose.tools.assert_equal(utils.input_int_default("bla", 42), 1337)


@nose.tools.raises(Exception)
def query_yes_no_exception_test():
    """Another Python 2/3 input hack."""
    try:
        import __builtin__
        builtins_str = "__builtin__"
    except ImportError:
        import builtins
        builtins_str = "builtins"
    with mock.patch('%s.raw_input' % builtins_str, return_value=''):
        utils.query_yes_no("bla", "asdf")


@nose.tools.raises(SystemExit)
def is_valid_file_test():
    """Check if a file exists. Do this check within ArgumentParser."""
    parser = argparse.ArgumentParser()

    # Does exist
    path = os.path.realpath(__file__)
    nose.tools.assert_equal(utils.is_valid_file(parser, path), path)

    # Does not exist
    utils.is_valid_file(parser, "/etc/nonexistingfile")


@nose.tools.raises(SystemExit)
def is_valid_folder_test():
    """Similiar to is_valid_file."""
    parser = argparse.ArgumentParser()

    # Does exist
    nose.tools.assert_equal(utils.is_valid_folder(parser, "/etc"), "/etc")

    # Does not exist
    utils.is_valid_folder(parser, "/etc/nonexistingfoler")


def create_project_configuration_test():
    """Test if the creation of the project configuration works."""
    filename = 'projectconftesttmp.txt'
    utils.create_project_configuration(filename)
    if os.path.isfile(filename):
        os.remove(filename)


def get_latest_model_test():
    """Check if get_latest_model works."""
    model_folder = "/etc"
    basename = "model"
    nose.tools.assert_equal(utils.get_latest_model(model_folder, basename),
                            None)
    small = os.path.join(utils.get_project_root(),
                         "models/small-baseline")
    utils.get_latest_model(small, basename)


def choose_raw_dataset_test():
    """Check the interactive function choose_raw_dataset."""
    try:
        import __builtin__
        with mock.patch('__builtin__.raw_input', return_value=0):
            utils.choose_raw_dataset()
    except ImportError:
        with mock.patch('builtins.input', return_value=0):
            utils.choose_raw_dataset()


def get_recognizer_folders_test():
    """Test if all folders are catched."""
    small = os.path.join(utils.get_project_root(),
                         "models/small-baseline")
    folders = utils.get_recognizer_folders(small)
    wanted_folders = ['preprocessed/small-baseline',
                      'feature-files/small',
                      'models/small-baseline']
    for folder, wanted_folder in zip(folders, wanted_folders):
        nose.tools.assert_equal(folder.endswith(wanted_folder),
                                True)


def load_model_test():
    """Test if the packaged model can be loaded."""
    model_path = pkg_resources.resource_filename('hwrt', 'misc/')
    model_file = os.path.join(model_path, "model.tar")
    utils.load_model(model_file)


def evaluate_model_single_recording_preloaded_test():
    """Test if the packaged model can be used."""
    model_path = pkg_resources.resource_filename('hwrt', 'misc/')
    model_file = os.path.join(model_path, "model.tar")
    recording = [[{'x': 12, 'y': 42, 'time': 123}]]
    utils.evaluate_model_single_recording(model_file, json.dumps(recording))
    (pq, fl, model, output_semantics) = utils.load_model(model_file)

    # data = {}
    # data['recording'] = json.dumps(recording)
    # data['preprocessing_queue'] = pq
    # data['feature_list'] = fl
    # data['model'] = model
    # data['output_semantics'] = output_semantics
    # utils.evaluate_model_single_recording_preloaded(**data)
