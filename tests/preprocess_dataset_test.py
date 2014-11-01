#!/usr/bin/env python
# -*- coding: utf-8 -*-

import nose
import os

# hwrt modules
import hwrt.preprocess_dataset as preprocess_dataset
import hwrt.utils as utils


# Tests
@nose.tools.nottest
def execution_test():
    small = os.path.join(utils.get_project_root(),
                         "preprocessed/small-baseline")
    preprocess_dataset.main(small)
