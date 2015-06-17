#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pkg_resources
import nose

# hwrt modules
import hwrt.filter_dataset as filter_dataset


# Tests
def main_execution_test():
    misc_path = pkg_resources.resource_filename('hwrt', 'misc/')
    tests_path = os.path.join(os.path.dirname(__file__), 'data/')
    symbol_yml_file = os.path.join(misc_path, 'symbols.yml')
    raw_pickle_file = os.path.join(tests_path, 'unittests-tiny-raw.pickle')
    pickle_dest_path = os.path.join(tests_path,
                                    'unittests-tiny-raw-filtered-tmp.pickle')
    filter_dataset.main(symbol_yml_file, raw_pickle_file, pickle_dest_path)


def get_parser_execution_test():
    filter_dataset.get_parser()


def get_metadata_test():
    metadata = filter_dataset.get_metadata()
    nose.tools.assert_equal(len(metadata), 3)
