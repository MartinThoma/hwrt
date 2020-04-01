#!/usr/bin/env python

"""Tests for the utility functions."""

# Core Library modules
import json
import os
from unittest import mock

# Third party modules
import pkg_resources
import pytest

# First party modules
import hwrt.preprocessing
import hwrt.utils as utils


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


def test_get_class():
    """The get_class function returns a class for feature and preprocessing
       algorithms.
    """
    utils.get_class("ScaleAndShift", "preprocessing", hwrt.preprocessing)

    with pytest.raises(ValueError):
        utils.get_class("BongaBonga", "preprocessing", hwrt.preprocessing)


def test_query_yes_no():
    """Get a binary decision by the user."""
    builtins_str = "builtins.input"
    with mock.patch(builtins_str, return_value="y"):
        assert utils.query_yes_no("bla")
        assert utils.query_yes_no("bla", None)
        assert utils.query_yes_no("bla", "yes")
        assert utils.query_yes_no("bla", "no")
    with mock.patch(builtins_str, return_value=""):
        assert utils.query_yes_no("bla", "yes")
        assert not utils.query_yes_no("bla", "no")


def test_input_int_default():
    builtins_str = "builtins.input"
    with mock.patch(builtins_str, return_value="yes"):
        assert utils.input_int_default("bla") == 0
        assert utils.input_int_default("bla", 42) == 42
    with mock.patch(builtins_str, return_value=1337):
        assert utils.input_int_default("bla") == 1337
        assert utils.input_int_default("bla", 42) == 1337


def test_query_yes_no_exception():
    with pytest.raises(Exception):
        import builtins  # noqa

        builtins_str = "builtins"
        with mock.patch("%s.raw_input" % builtins_str, return_value=""):
            utils.query_yes_no("bla", "asdf")


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
    import builtins  # noqa

    with mock.patch("builtins.input", return_value=0):
        utils.choose_raw_dataset()


@pytest.mark.skip(reason="This is an integration test with hwr-experiments")
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
