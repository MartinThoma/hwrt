#!/usr/bin/env python

"""Utility functions that can be used in multiple scripts."""

import logging
import sys
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)
import os
import yaml
import natsort
import time
import datetime
# mine
import preprocess_dataset
import create_pfiles
import create_model


def print_status(total, current, start_time=None):
    """Show how much work was done / how much work is remaining"""
    percentage_done = float(current)/total
    sys.stdout.write("\r%0.2f%% " % (percentage_done*100))
    if start_time is not None:
        current_running_time = time.time() - start_time
        remaining_seconds = current_running_time / percentage_done
        tmp = datetime.timedelta(seconds=remaining_seconds)
        sys.stdout.write("(%s remaining)   " % str(tmp))
    sys.stdout.flush()


def is_valid_file(parser, arg):
    """Check if arg is a valid file that already exists on the file system."""
    arg = os.path.abspath(arg)
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg


def is_valid_folder(parser, arg):
    """Check if arg is a valid file that already exists on the file system."""
    arg = os.path.abspath(arg)
    if not os.path.isdir(arg):
        parser.error("The folder %s does not exist!" % arg)
    else:
        return arg


def get_project_configuration():
    """Get project configuration as dictionary."""
    home = os.path.expanduser("~")
    rcfile = os.path.join(home, ".writemathrc")
    if not os.path.isfile(rcfile):
        create_project_configuration(rcfile)
    with open(rcfile, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    return cfg


def create_project_configuration(filename):
    home = os.path.expanduser("~")
    writemath = os.path.join(home, "writemath")
    config = {'root': writemath,
              'nntoolkit': None,
              'dropbox_app_key': None,
              'dropbox_app_secret': None}
    with open(filename, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


def get_project_root():
    """Get the project root folder as a string."""
    cfg = get_project_configuration()
    return cfg['root']


def get_nntoolkit():
    """Get the project root folder as a string."""
    cfg = get_project_configuration()
    return cfg['nntoolkit']


def get_latest_in_folder(folder, ending="", default=""):
    """Get the file that comes last with natural sorting in folder and has
       file ending 'ending'.
    """
    latest = default
    for my_file in natsort.natsorted(os.listdir(folder), reverse=True):
        if my_file.endswith(ending):
            latest = os.path.join(folder, my_file)
    return latest


def get_latest_folder(folder):
    """Get the absolute path of a subfolder that comes last with natural
       sorting in the given folder.
    """
    folders = [os.path.join(folder, name) for name in os.listdir(folder)
               if os.path.isdir(os.path.join(folder, name))]
    folders = natsort.natsorted(folders, reverse=True)
    return os.path.abspath(folders[0])


def get_database_config_file():
    """Get the absolute path to the database configuration file."""
    return os.path.join(get_project_root(), "tools/db.config.yml")


def get_database_configuration():
    """Get database configuration as dictionary."""
    with open(get_database_config_file(), 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    return cfg


def sizeof_fmt(num):
    """Takes the a filesize in bytes and returns a nicely formatted string. """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def input_string(question=""):
    """A function that works for both, Python 2.x and Python 3.x.
       It asks the user for input and returns it as a string.
    """
    import sys
    if sys.version_info[0] == 2:
        return raw_input(question)
    else:
        return input(question)


def input_int_default(question="", default=0):
    """A function that works for both, Python 2.x and Python 3.x.
       It asks the user for input and returns it as a string.
    """
    answer = input_string(question)
    if answer == "" or answer == "yes":
        return default
    else:
        return int(answer)


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input_string().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def get_latest_model(model_folder, basename):
    models = filter(lambda n: n.endswith(".json"), os.listdir(model_folder))
    models = filter(lambda n: n.startswith(basename), models)
    models = natsort.natsorted(models, reverse=True)
    if len(models) == 0:
        return None
    else:
        return os.path.join(model_folder, models[-1])


def get_latest_working_model(model_folder):
    """Get the latest working model. Delete all others that get touched."""
    i = 0
    latest_model = ""
    while latest_model == "" and i < 5:
        latest_model = get_latest_in_folder(model_folder, ".json")
        # Cleanup in case a training was broken
        if os.path.isfile(latest_model) and os.path.getsize(latest_model) < 10:
            os.remove(latest_model)
            latest_model = ""
        i += 1
    return latest_model


def get_latest_successful_run(folder):
    """Get the latest successful run timestamp."""
    runfile = os.path.join(folder, "run.log")
    if not os.path.isfile(runfile):
        return None
    with open(runfile) as f:
        content = f.readlines()
    return datetime.datetime.strptime(content[0],
                                      "timestamp: '%Y-%m-%d %H:%M:%S'")


def create_run_logfile(folder):
    """Create a 'run.log' within folder. This file contains the time of the
       latest successful run.
    """
    with open(os.path.join(folder, "run.log"), "w") as f:
        datestring = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        f.write("timestamp: '%s'" % datestring)


def update_if_outdated(folder):
    """Check if the currently watched instance (model, feature or
        preprocessing) is outdated and update it eventually.
    """

    folders = []
    while os.path.isdir(folder):
        folders.append(folder)
        # Get info.yml
        with open(os.path.join(folder, "info.yml")) as ymlfile:
            content = yaml.load(ymlfile)
        folder = os.path.join(get_project_root(), content['data-source'])
    raw_source_file = folder
    dt = os.path.getmtime(raw_source_file)
    source_mtime = datetime.datetime.utcfromtimestamp(dt)
    folders = folders[::-1]  # Reverse order to get the most "basic one first"

    for target_folder in folders:
        target_mtime = get_latest_successful_run(target_folder)
        if target_mtime is None or source_mtime > target_mtime:
            # The source is later than the target. That means we need to
            # refresh the target
            if "preprocessed" in target_folder:
                logging.info("Preprocessed file was outdated. Update...")
                preprocess_dataset.main(os.path.join(get_project_root(),
                                                     target_folder))
            elif "feature-files" in target_folder:
                logging.info("Feature file was outdated. Update...")
                create_pfiles.main(target_folder)
            elif "model" in target_folder:
                logging.info("Model file was outdated. Update...")
                create_model.main(target_folder, True)
            target_mtime = datetime.datetime.utcnow()
        else:
            logging.info("'%s' is up-to-date.", target_folder)
        source_mtime = target_mtime


def choose_raw_dataset(currently=""):
    """Let the user choose a raw dataset. Return the absolute path."""
    folder = os.path.join(get_project_root(), "archive/raw-datasets")
    files = [os.path.join(folder, name) for name in os.listdir(folder)
             if name.endswith(".pickle")]
    default = -1
    for i, filename in enumerate(files):
        if os.path.basename(currently) == os.path.basename(filename):
            default = i
        if i != default:
            print("[%i]\t%s" % (i, os.path.basename(filename)))
        else:
            print("\033[1m[%i]\033[0m\t%s" % (i, os.path.basename(filename)))
    i = input_int_default("Choose a dataset by number: ", default)
    return files[i]


def get_readable_time(t):
    """ Format the time to a readable format.
    :param t: Time in ms
    :returns: string that has the time splitted to highest used time
            (minutes, hours, ...)
    :rtype: string
    """
    ms = t % 1000
    t -= ms
    t /= 1000

    s = t % 60
    t -= s
    t /= 60

    minutes = t % 60
    t -= minutes
    t /= 60

    if t != 0:
        return "%ih, %i minutes %is %ims" % (t, minutes, s, ms)
    elif minutes != 0:
        return "%i minutes %is %ims" % (minutes, s, ms)
    elif s != 0:
        return "%is %ims" % (s, ms)
    else:
        return "%ims" % ms
