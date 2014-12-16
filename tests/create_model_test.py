#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

# hwrt modules
import hwrt.create_model as create_model
import hwrt.utils as utils


# Tests
def execution_test():
    small = os.path.join(utils.get_project_root(), "models/small-baseline")
    create_model.main(small)


def parser_test():
    create_model.get_parser()
