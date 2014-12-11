#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nose.plugins.skip import SkipTest
import shutil
import os

# hwrt modules
import hwrt.view as view
import hwrt.utils as utils


# Tests
def execution_test():
    view.get_parser()
    view._fetch_data_from_server(31, 'mysql_online')

    d = os.path.dirname(__file__)
    target = os.path.join(utils.get_project_root(),
                          'raw-datasets/unittests-tiny-raw.pickle')
    shutil.copyfile(os.path.join(d, 'data/unittests-tiny-raw.pickle'),
                    target)
    view._get_data_from_rawfile(target, 345)  # Is in tiny test set
    view._get_data_from_rawfile(target, 42)  # Is not in tiny test set
    view._list_ids(target)
    model_folder = os.path.join(utils.get_project_root(),
                                'models/small-baseline')
    view._get_system(model_folder)
    #display_data(raw_data_string, raw_data_id, model_folder, show_raw)


@SkipTest
def execute_main_test():
    model_small = os.path.join(utils.get_project_root(),
                               "models",
                               "small-baseline")
    view.main(True, model_small, False, 31, False, 'mysql_online')
    view.main(False, model_small, False, 31, False, 'mysql_online')
    view.main(False, model_small, True, 31, False, 'mysql_online')
    view.main(False, model_small, False, 31, True, 'mysql_online')

    # with patch('sys.exit') as exit_mock:
    #     view._get_description('.')
    #     assert exit_mock.called
