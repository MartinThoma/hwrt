#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Check if all necessary modules / programs / files for HWRT are there and
   if the version is ok.
"""

import imp
import sys
import platform
import os
import pkg_resources

# hwrt
from . import utils


class bcolors(object):
    """Terminal colors with ANSI escape codes."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def which(program):
    """Get the path of a program or ``None`` if ``program`` is not in path."""
    def is_exe(fpath):
        """Check for windows users."""
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def check_python_version():
    """Check if the currently running Python version is new enough."""
    # Required due to multiple with statements on one line
    req_version = (2, 7)
    cur_version = sys.version_info
    if cur_version >= req_version:
        print("Python version... %sOK%s (found %s, requires %s)" %
              (bcolors.OKGREEN, bcolors.ENDC, str(platform.python_version()),
               str(req_version[0]) + "." + str(req_version[1])))
    else:
        print("Python version... %sFAIL%s (found %s, requires %s)" %
              (bcolors.FAIL, bcolors.ENDC, str(cur_version),
               str(req_version)))


def check_python_modules():
    """Check if all necessary / recommended modules are installed."""
    print("\033[1mCheck modules\033[0m")
    required_modules = ['argparse', 'matplotlib', 'natsort', 'pymysql',
                        'cPickle', 'theano', 'dropbox', 'yaml',
                        'webbrowser', 'hashlib', 'numpy',
                        'jinja2']
    found = []
    for required_module in required_modules:
        try:
            imp.find_module(required_module)
            check = "module '%s' ... %sfound%s" % (required_module,
                                                   bcolors.OKGREEN,
                                                   bcolors.ENDC)
            print(check)
            found.append(required_module)
        except ImportError:
            print("module '%s' ... %sNOT%s found" % (required_module,
                                                     bcolors.WARNING,
                                                     bcolors.ENDC))

    if "argparse" in found:
        import argparse
        print("argparse version: %s (1.1 tested)" % argparse.__version__)
    if "matplotlib" in found:
        import matplotlib
        print("matplotlib version: %s (1.2.1 tested)" % matplotlib.__version__)
    if "natsort" in found:
        import natsort
        print("natsort version: %s (3.4.0 tested, 3.4.0 > required)" %
              natsort.__version__)
    if "pymysql" in found:
        import pymysql
        print("pymysql version: %s (0.6.3 tested)" %
              pymysql.__version__)
    if "theano" in found:
        import theano
        print("theano version: %s (0.6.0 tested)" %
              theano.__version__)
    if "numpy" in found:
        import numpy
        print("numpy version: %s (1.8.1 tested)" %
              numpy.__version__)
    if "yaml" in found:
        import yaml
        print("yaml version: %s (3.11 tested)" %
              yaml.__version__)
    if "jinja2" in found:
        import jinja2
        print("jinja2 version: %s (2.7.3 tested)" %
              jinja2.__version__)
    if "cPickle" in found:
        import cPickle
        print("cPickle version: %s (1.71 tested)" %
              cPickle.__version__)
        print("cPickle HIGHEST_PROTOCOL: %s (2 required)" %
              cPickle.HIGHEST_PROTOCOL)


def check_executables():
    """Check if all necessary / recommended executables are installed."""
    print("\033[1mCheck executables\033[0m")
    required_executables = ["pfile_create", utils.get_nntoolkit()]
    for executable in required_executables:
        path = which(executable)
        if path is None:
            print("%s ... %sNOT%s found" % (executable, bcolors.WARNING,
                                            bcolors.ENDC))
            print("Try 'http://martin-thoma.com/what-are-pfiles/' for "
                  "instructions how to get it.")
        else:
            print("%s ... %sfound%s at %s" % (executable, bcolors.OKGREEN,
                                              bcolors.ENDC, path))


def main():
    """Execute all checks."""
    check_python_version()
    check_python_modules()
    check_executables()
    home = os.path.expanduser("~")
    print("\033[1mCheck files\033[0m")
    rcfile = os.path.join(home, ".hwrtrc")
    if os.path.isfile(rcfile):
        print("~/.hwrtrc... %sFOUND%s" %
              (bcolors.OKGREEN, bcolors.ENDC))
    else:
        print("~/.hwrtrc... %sNOT FOUND%s" %
              (bcolors.FAIL, bcolors.ENDC))
    misc_path = pkg_resources.resource_filename('hwrt', 'misc/')
    print("misc-path: %s" % misc_path)


if __name__ == '__main__':
    main()
