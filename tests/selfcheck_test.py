#!/usr/bin/env python

# First party modules
import hwrt.selfcheck as selfcheck


def test_execution():
    # selfcheck.main()
    selfcheck.check_python_version()
    selfcheck.check_python_modules()


def test_which():
    return_value = selfcheck.which("somethingthatdoesntexist")
    assert return_value is None
    return_value = selfcheck.which("/home/somethingthatdoesntexist")
    assert return_value is None
    return_value = selfcheck.which("/bin/ls")
    assert return_value == "/bin/ls"
