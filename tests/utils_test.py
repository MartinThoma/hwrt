#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the utility functions."""

# Core Library modules
import argparse
import json
import os

# Third party modules
import pkg_resources
import pytest

# First party modules
import hwrt.preprocessing
import hwrt.utils as utils

try:
    from unittest import mock  # Python 3
except ImportError:
    import mock  # Python 2


def test_execution():
    """Test if the functions execute at all."""
    utils.get_project_root()
    utils.get_latest_model(".", "model")
    utils.get_latest_working_model(".")
    utils.get_latest_successful_run(".")
    assert utils.get_readable_time(123) == "123ms"
    assert utils.get_readable_time(1000 * 30) == "30s 0ms"
    assert utils.get_readable_time(1000 * 60) == "1 minutes 0s 0ms"
    assert utils.get_readable_time(1000 * 60 * 60) == "1h, 0 minutes 0s 0ms"
    assert utils.get_readable_time(2 * 1000 * 60 * 60) == "2h, 0 minutes 0s 0ms"
    assert utils.get_readable_time(25 * 1000 * 60 * 60 + 3) == "25h, 0 minutes 0s 3ms"
    utils.print_status(3, 1, 123)
    utils.get_nntoolkit()
    utils.get_database_config_file()
    utils.get_database_configuration()
    assert utils.sizeof_fmt(1) == "1.0 bytes"
    assert utils.sizeof_fmt(1111) == "1.1 KB"


def test_parser():
    """Check the parser."""
    from argparse import ArgumentParser

    parser = ArgumentParser()
    home = os.path.expanduser("~")
    rcfile = os.path.join(home, ".hwrtrc")
    parser.add_argument(
        "-m", "--model", dest="model", type=lambda x: utils.is_valid_folder(parser, x)
    )
    parser.parse_args(["-m", home])

    parser = ArgumentParser()
    parser.add_argument(
        "-m", "--model", dest="model", type=lambda x: utils.is_valid_file(parser, x)
    )
    parser.parse_args(["-m", rcfile])


def test_get_class():
    """The get_class function returns a class for feature and preprocessing
       algorithms.
    """
    utils.get_class("ScaleAndShift", "preprocessing", hwrt.preprocessing)
    utils.get_class("BongaBonga", "preprocessing", hwrt.preprocessing)


def test_query_yes_no():
    """This function is used to get a binary decision by the user.
       Sadly, there are two different ways to use it due to Python 2 / 3.
    """
    try:
        import __builtin__  # noqa

        builtins_str = "__builtin__.raw_input"
    except ImportError:
        builtins_str = "builtins.input"
    with mock.patch("%s" % builtins_str, return_value="y"):
        assert utils.query_yes_no("bla")
        assert utils.query_yes_no("bla", None)
        assert utils.query_yes_no("bla", "yes")
        assert utils.query_yes_no("bla", "no")
    with mock.patch("%s" % builtins_str, return_value=""):
        assert utils.query_yes_no("bla", "yes")
        assert not utils.query_yes_no("bla", "no")


def test_input_string():
    """Another Python 2/3 input hack."""
    try:
        import __builtin__  # noqa

        with mock.patch("__builtin__.raw_input", return_value="y"):
            assert utils.input_string("bla") == "y"
    except ImportError:
        with mock.patch("builtins.input", return_value="y"):
            assert utils.input_string("bla") == "y"


def test_input_int_default():
    """Another Python 2/3 input hack."""
    try:
        import __builtin__  # noqa

        builtins_str = "__builtin__.raw_input"
    except ImportError:
        builtins_str = "builtins.input"
    with mock.patch("%s" % builtins_str, return_value="yes"):
        assert utils.input_int_default("bla") == 0
        assert utils.input_int_default("bla", 42) == 42
    with mock.patch("%s" % builtins_str, return_value=1337):
        assert utils.input_int_default("bla") == 1337
        assert utils.input_int_default("bla", 42) == 1337


def test_query_yes_no_exception():
    """Another Python 2/3 input hack."""
    with pytest.raises(Exception):
        try:
            import __builtin__  # noqa

            builtins_str = "__builtin__"
        except ImportError:
            import builtins  # noqa

            builtins_str = "builtins"
        with mock.patch("%s.raw_input" % builtins_str, return_value=""):
            utils.query_yes_no("bla", "asdf")


def is_valid_file_test():
    """Check if a file exists. Do this check within ArgumentParser."""
    with pytest.raises(SystemExit):
        parser = argparse.ArgumentParser()

        # Does exist
        path = os.path.realpath(__file__)
        assert utils.is_valid_file(parser, path) == path

        # Does not exist
        utils.is_valid_file(parser, "/etc/nonexistingfile")


def test_is_valid_folder():
    """Similiar to is_valid_file."""
    with pytest.raises(SystemExit):
        parser = argparse.ArgumentParser()

        # Does exist
        assert utils.is_valid_folder(parser, "/etc") == "/etc"

        # Does not exist
        utils.is_valid_folder(parser, "/etc/nonexistingfoler")


def test_create_project_configuration():
    """Test if the creation of the project configuration works."""
    filename = "projectconftesttmp.txt"
    utils.create_project_configuration(filename)
    if os.path.isfile(filename):
        os.remove(filename)


def test_get_latest_model():
    """Check if get_latest_model works."""
    model_folder = "/etc"
    basename = "model"
    assert utils.get_latest_model(model_folder, basename) is None
    small = os.path.join(utils.get_project_root(), "models/small-baseline")
    utils.get_latest_model(small, basename)


def test_choose_raw_dataset():
    """Check the interactive function choose_raw_dataset."""
    try:
        import __builtin__  # noqa

        with mock.patch("__builtin__.raw_input", return_value=0):
            utils.choose_raw_dataset()
    except ImportError:
        import builtins  # noqa

        with mock.patch("builtins.input", return_value=0):
            utils.choose_raw_dataset()


def test_get_recognizer_folders():
    """Test if all folders are catched."""
    small = os.path.join(utils.get_project_root(), "models/small-baseline")
    folders = utils.get_recognizer_folders(small)
    wanted_folders = [
        "preprocessed/small-baseline",
        "feature-files/small",
        "models/small-baseline",
    ]
    for folder, wanted_folder in zip(folders, wanted_folders):
        assert folder.endswith(wanted_folder)


def test_load_model():
    """Test if the packaged model can be loaded."""
    model_path = pkg_resources.resource_filename("hwrt", "misc/")
    model_file = os.path.join(model_path, "model.tar")
    utils.load_model(model_file)


def test_evaluate_model_single_recording_preloaded():
    """Test if the packaged model can be used."""
    model_path = pkg_resources.resource_filename("hwrt", "misc/")
    model_file = os.path.join(model_path, "model.tar")
    recording = [[{"x": 12, "y": 42, "time": 123}]]
    utils.evaluate_model_single_recording(model_file, json.dumps(recording))
    (pq, fl, model, output_semantics) = utils.load_model(model_file)

    # data = {}
    # data['recording'] = json.dumps(recording)
    # data['preprocessing_queue'] = pq
    # data['feature_list'] = fl
    # data['model'] = model
    # data['output_semantics'] = output_semantics
    # utils.evaluate_model_single_recording_preloaded(**data)
