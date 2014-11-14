#!/usr/bin/env python
# -*- coding: utf-8 -*-

import nose

# hwrt modules
import hwrt.selfcheck as selfcheck


# Tests
@SkipTest
def execution_test():
    selfcheck.main()


def which_test():
    return_value = selfcheck.which("somethingthatdoesntexist")
    nose.tools.assert_equal(return_value, None)
    return_value = selfcheck.which("/home/somethingthatdoesntexist")
    nose.tools.assert_equal(return_value, None)
    return_value = selfcheck.which("/bin/ls")
    nose.tools.assert_equal(return_value, "/bin/ls")
