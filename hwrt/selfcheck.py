#!/usr/bin/env python

"""Check if all necessary modules / programs / files for HWRT are there and
   if the version is ok.
"""

# Core Library modules
import importlib
import os
import platform
import sys

# Third party modules
import pkg_resources

# Local modules
# hwrt
from . import utils


class Bcolors:
    """Terminal colors with ANSI escape codes."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"


def which(program):
    """Get the path of a program or ``None`` if ``program`` is not in path."""
    if program is None:
        return None

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
        print(
            "Python version... %sOK%s (found %s, requires %s)"
            % (
                Bcolors.OKGREEN,
                Bcolors.ENDC,
                str(platform.python_version()),
                str(req_version[0]) + "." + str(req_version[1]),
            )
        )
    else:
        print(
            "Python version... %sFAIL%s (found %s, requires %s)"
            % (Bcolors.FAIL, Bcolors.ENDC, str(cur_version), str(req_version))
        )


def check_python_modules():
    """Check if all necessary / recommended modules are installed."""
    print("\033[1mCheck modules\033[0m")
    required_modules = [
        "click",
        "cPickle",
        "dropbox",
        "hashlib",
        "jinja2",
        "matplotlib",
        "natsort",
        "numpy",
        "pymysql",
        "webbrowser",
        "yaml",
    ]
    found = []
    for required_module in required_modules:
        toolbox_specs = importlib.util.find_spec(required_module)
        if toolbox_specs is None:
            print(
                "module '%s' ... %sNOT%s found"
                % (required_module, Bcolors.WARNING, Bcolors.ENDC)
            )
        else:
            toolbox = importlib.util.module_from_spec(toolbox_specs)
            toolbox_specs.loader.exec_module(toolbox)

            check = "module '{}' ... {}found{}".format(
                required_module, Bcolors.OKGREEN, Bcolors.ENDC,
            )
            print(check)
            found.append(required_module)

    if "click" in found:
        import click

        print("click version: %s (NONE tested)" % click.__version__)
    if "matplotlib" in found:
        import matplotlib

        print("matplotlib version: %s (1.2.1 tested)" % matplotlib.__version__)
    if "natsort" in found:
        import natsort

        print(
            "natsort version: %s (3.4.0 tested, 3.4.0 > required)" % natsort.__version__
        )
    if "pymysql" in found:
        import pymysql

        print("pymysql version: %s (0.6.3 tested)" % pymysql.__version__)
    if "numpy" in found:
        import numpy

        print("numpy version: %s (1.8.1 tested)" % numpy.__version__)
    if "yaml" in found:
        import yaml

        print("yaml version: %s (3.11 tested)" % yaml.__version__)
    if "jinja2" in found:
        import jinja2

        print("jinja2 version: %s (2.7.3 tested)" % jinja2.__version__)
    if "cPickle" in found:
        import cPickle

        print("cPickle version: %s (1.71 tested)" % cPickle.__version__)
        print("cPickle HIGHEST_PROTOCOL: %s (2 required)" % cPickle.HIGHEST_PROTOCOL)


def check_executables():
    """Check if all necessary / recommended executables are installed."""
    print("\033[1mCheck executables\033[0m")
    required_executables = [("nntoolkit", utils.get_nntoolkit())]
    for name, executable in required_executables:
        path = which(executable)
        if path is None:
            print(
                "%s (%s) ... %sNOT%s found"
                % (name, executable, Bcolors.WARNING, Bcolors.ENDC)
            )
        else:
            print(
                "%s ... %sfound%s at %s"
                % (executable, Bcolors.OKGREEN, Bcolors.ENDC, path)
            )


def main():
    """Execute all checks."""
    check_python_version()
    check_python_modules()
    check_executables()
    home = os.path.expanduser("~")
    print("\033[1mCheck files\033[0m")
    rcfile = os.path.join(home, ".hwrtrc")
    if os.path.isfile(rcfile):
        print(f"~/.hwrtrc... {Bcolors.OKGREEN}FOUND{Bcolors.ENDC}")
    else:
        print(f"~/.hwrtrc... {Bcolors.FAIL}NOT FOUND{Bcolors.ENDC}")
    misc_path = pkg_resources.resource_filename("hwrt", "misc/")
    print("misc-path: %s" % misc_path)
