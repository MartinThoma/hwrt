#!/usr/bin/env python
# -*- coding: utf-8 -*-

import nose
import mock

# hwrt modules
import hwrt
import hwrt.utils as utils


# Tests
def execution_test():
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
    from argparse import ArgumentParser
    import os
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
    utils.get_class('ScaleAndShift', 'preprocessing', hwrt.preprocessing)
    utils.get_class('BongaBonga', 'preprocessing', hwrt.preprocessing)


def query_yes_no_test():
    with mock.patch('__builtin__.raw_input', return_value='y'):
        nose.tools.assert_equal(utils.query_yes_no("bla"), True)
        nose.tools.assert_equal(utils.query_yes_no("bla", None), True)
        nose.tools.assert_equal(utils.query_yes_no("bla", "yes"), True)
        nose.tools.assert_equal(utils.query_yes_no("bla", "no"), True)
    with mock.patch('__builtin__.raw_input', return_value=''):
        nose.tools.assert_equal(utils.query_yes_no("bla", 'yes'), True)
        nose.tools.assert_equal(utils.query_yes_no("bla", 'no'), False)


@nose.tools.raises(Exception)
def query_yes_no_exception_test():
    with mock.patch('__builtin__.raw_input', return_value=''):
        utils.query_yes_no("bla", "asdf")
