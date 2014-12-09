#!/usr/bin/env python

"""Utility functions that can be used in multiple scripts."""

from __future__ import print_function
import inspect
import imp
import logging
import sys
import os
import yaml
import natsort
import time
import datetime
import subprocess
import shutil
import csv
import pkg_resources
import tempfile
import tarfile

# hwrt modules
from . import HandwrittenData


def print_status(total, current, start_time=None):
    """Show how much work was done / how much work is remaining
    :param total: The total amount of work
    :type total: float
    :param current: The work that has been done so far
    :type current: float
    :param start_time: The start time in seconds since 1970 to estimate the
                       remaining time."""
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
    rcfile = os.path.join(home, ".hwrtrc")
    if not os.path.isfile(rcfile):
        create_project_configuration(rcfile)
    with open(rcfile, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    return cfg


def create_project_configuration(filename):
    """Create a project configuration file which contains a configuration
       that might make sense."""
    home = os.path.expanduser("~")
    project_root_folder = os.path.join(home, "hwr-experiments")
    config = {'root': project_root_folder,
              'nntoolkit': None,
              'dropbox_app_key': None,
              'dropbox_app_secret': None,
              'dbconfig': os.path.join(home, "hwrt-config/db.config.yml"),
              'data_analyzation_queue': [{'Creator': None}]}
    with open(filename, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


def get_project_root():
    """Get the project root folder as a string."""
    cfg = get_project_configuration()
    # At this point it can be sure that the configuration file exists
    # Now make sure the project structure exists
    for dirname in ["raw-datasets",
                    "preprocessed",
                    "feature-files",
                    "models",
                    "reports"]:
        directory = os.path.join(cfg['root'], dirname)
        if not os.path.exists(directory):
            os.makedirs(directory)

    raw_yml_path = pkg_resources.resource_filename('hwrt', 'misc/')

    # TODO: How to check for updates if it already exists?
    raw_data_dst = os.path.join(cfg['root'], "raw-datasets/info.yml")
    if not os.path.isfile(raw_data_dst):
        raw_yml_pkg_src = os.path.join(raw_yml_path, "info.yml")
        shutil.copy(raw_yml_pkg_src, raw_data_dst)

    # Make sure small-baseline folders exists
    for dirname in ["models/small-baseline", "feature-files/small-baseline",
                    "preprocessed/small-baseline"]:
        directory = os.path.join(cfg['root'], dirname)
        if not os.path.exists(directory):
            os.makedirs(directory)

    # Make sure small-baseline yml files exist
    paths = [("preprocessed/small-baseline/", "preprocessing-small-info.yml"),
             ("feature-files/small-baseline/", "feature-small-info.yml"),
             ("models/small-baseline/", "model-small-info.yml")]
    for dest, src in paths:
        raw_data_dst = os.path.join(cfg['root'], "%s/info.yml" % dest)
        if not os.path.isfile(raw_data_dst):
            raw_yml_pkg_src = os.path.join(raw_yml_path, src)
            shutil.copy(raw_yml_pkg_src, raw_data_dst)

    return cfg['root']


def get_template_folder():
    """Get path to the folder where th HTML templates are."""
    cfg = get_project_configuration()
    if 'templates' not in cfg:
        home = os.path.expanduser("~")
        rcfile = os.path.join(home, ".hwrtrc")
        cfg['templates'] = pkg_resources.resource_filename('hwrt',
                                                           'templates/')
        with open(rcfile, 'w') as f:
            yaml.dump(cfg, f, default_flow_style=False)
    return cfg['templates']


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
    if len(folders) == 0:
        # No model folder!
        logging.error("You don't have any model folder. I suggest you "
                      "have a look at "
                      "https://github.com/MartinThoma/hwr-experiments and "
                      "http://hwrt.readthedocs.org/")
        sys.exit(-1)
    else:
        return os.path.abspath(folders[0])


def get_database_config_file():
    """Get the absolute path to the database configuration file."""
    cfg = get_project_configuration()
    if 'dbconfig' in cfg:
        if os.path.isfile(cfg['dbconfig']):
            return cfg['dbconfig']
        else:
            logging.info("File '%s' was not found. Adjust 'dbconfig' in your "
                         "~/.hwrtrc file.",
                         cfg['dbconfig'])
    else:
        logging.info("No database connection file found. "
                     "Specify 'dbconfig' in your ~/.hwrtrc file.")
    return None


def get_database_configuration():
    """Get database configuration as dictionary."""
    db_config = get_database_config_file()
    if db_config is None:
        return None
    with open(db_config, 'r') as ymlfile:
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
    """Get the latest model (determined by the name of the model in
       natural sorted order) which begins with ``basename``."""
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

    from . import preprocess_dataset
    from . import create_pfiles
    from . import create_model

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
    folder = os.path.join(get_project_root(), "raw-datasets")
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


def default_model():
    """Get a path for a default value for the model. Start searching in the
    current directory."""
    project_root = get_project_root()
    models_dir = os.path.join(project_root, "models")
    curr_dir = os.getcwd()
    if os.path.commonprefix([models_dir, curr_dir]) == models_dir and \
       curr_dir != models_dir:
        latest_model = curr_dir
    else:
        latest_model = get_latest_folder(models_dir)
    return latest_model


def create_adjusted_model_for_percentages(model_src, model_use):
    """Replace logreg layer by sigmoid to get probabilities."""
    # Copy model file
    shutil.copyfile(model_src, model_use)
    # Adjust model file
    with open(model_src) as f:
        content = f.read()
    content = content.replace("logreg", "sigmoid")
    with open(model_use, "w") as f:
        f.write(content)


def create_pfile(output_filename, feature_count, data):
    """Create a pfile.
    :param output_filename: name of the pfile that will be created
    :param feature_count: dimension of all features combined
    :type feature_count: int
    :param data: list of (x, y) tuples, where x is the feature vector
                 of dimension ``feature_count`` and y is a label.
    """
    f = tempfile.NamedTemporaryFile(delete=False)
    input_filename = f.name

    for symbolnr, instance in enumerate(data):
        feature_string, label = instance
        assert len(feature_string) == feature_count, \
            "Expected %i features, got %i features" % \
            (feature_count, len(feature_string))
        feature_string = " ".join(map(str, feature_string))
        line = "%i 0 %s %i" % (symbolnr, feature_string, label)
        print(line, file=f)
    f.close()

    command = "pfile_create -i %s -f %i -l 1 -o %s" % \
              (input_filename, feature_count, output_filename)
    logging.info(command)
    return_code = os.system(command)
    if return_code != 0:
        logging.error("pfile_create failed with return code %i.", return_code)
        sys.exit(-1)

    # Cleanup
    os.remove(input_filename)


def get_recognizer_folders(model_folder):
    """Get a list of folders [preprocessed, feature-files, model]."""
    folders = []
    folder = model_folder
    while os.path.isdir(folder):
        folders.append(folder)
        # Get info.yml
        with open(os.path.join(folder, "info.yml")) as ymlfile:
            content = yaml.load(ymlfile)
        folder = os.path.join(get_project_root(), content['data-source'])
    return folders[::-1]  # Reverse order to get the most "basic one first"


def load_model(model_file):
    """Load a model by its file. This includes the model itself, but also
       the preprocessing queue, the feature list and the output semantics.
    """
    # Extract tar
    tar = tarfile.open(model_file)
    tarfolder = tempfile.mkdtemp()
    tar.extractall(path=tarfolder)
    tar.close()

    from . import features
    from . import preprocessing

    # Get the preprocessing
    with open(os.path.join(tarfolder, "preprocessing.yml"), 'r') as ymlfile:
        preprocessing_description = yaml.load(ymlfile)
    tmp = preprocessing_description['queue']
    preprocessing_queue = preprocessing.get_preprocessing_queue(tmp)

    # Get the features
    with open(os.path.join(tarfolder, "features.yml"), 'r') as ymlfile:
        feature_description = yaml.load(ymlfile)
    feature_str_list = feature_description['features']
    feature_list = features.get_features(feature_str_list)

    # Get the model
    import nntoolkit.evaluate
    model = nntoolkit.evaluate.get_model(model_file)

    output_semantics_file = os.path.join(tarfolder, 'output_semantics.csv')
    output_semantics = nntoolkit.evaluate.get_outputs(output_semantics_file)

    # Cleanup
    shutil.rmtree(tarfolder)

    return (preprocessing_queue, feature_list, model, output_semantics)


def evaluate_model_single_recording_preloaded(preprocessing_queue,
                                              feature_list,
                                              model,
                                              output_semantics,
                                              recording):
    """Evaluate a model for a single recording, after everything has been
       loaded.
    :param preprocessing_queue: List of all preprocessing objects.
    :param feature_list: List of all feature objects.
    :param model: Neural network model.
    :param output_semantics: List that defines what an output means.
    :param recording: The handwritten recording in JSON format.
    """
    handwriting = HandwrittenData.HandwrittenData(recording)
    handwriting.preprocessing(preprocessing_queue)
    x = handwriting.feature_extraction(feature_list)
    import nntoolkit.evaluate
    model_output = nntoolkit.evaluate.get_model_output(model, [x])
    return nntoolkit.evaluate.get_results(model_output, output_semantics)


def evaluate_model_single_recording(model_file, recording):
    """Evaluate a model for a single recording.
    :param model_file: Model file (.tar)
    :param recording: The handwritten recording.
    """
    (preprocessing_queue, feature_list, model,
     output_semantics) = load_model(model_file)
    results = evaluate_model_single_recording_preloaded(preprocessing_queue,
                                                        feature_list,
                                                        model,
                                                        output_semantics,
                                                        recording)
    return results


def _evaluate_model_single_file(target_folder, test_file):
    """Evaluate a model for a single recording.
    :param target_folder: Folder where the model is
    :param test_file: The test file
    """
    logging.info("Create running model...")
    model_src = get_latest_model(target_folder, "model")
    model_file_pointer = tempfile.NamedTemporaryFile(delete=False)
    model_use = model_file_pointer.name
    model_file_pointer.close()
    logging.info("Adjusted model is in %s.", model_use)
    create_adjusted_model_for_percentages(model_src, model_use)

    # Run evaluation
    project_root = get_project_root()
    time_prefix = time.strftime("%Y-%m-%d-%H-%M")
    logging.info("Evaluate '%s' with '%s'...", model_src, test_file)
    logfilefolder = os.path.join(project_root, "logs/")
    if not os.path.exists(logfilefolder):
        os.makedirs(logfilefolder)
    logfile = os.path.join(project_root,
                           "logs/%s-error-evaluation.log" %
                           time_prefix)
    with open(logfile, "w") as log, open(model_use, "r") as modl_src_p:
        p = subprocess.Popen([get_nntoolkit(), 'run',
                              '--batch-size', '1',
                              '-f%0.4f', test_file],
                             stdin=modl_src_p,
                             stdout=log)
        ret = p.wait()
        if ret != 0:
            logging.error("nntoolkit finished with ret code %s",
                          str(ret))
            sys.exit()
    return (logfile, model_use)


def evaluate_model(recording, model_folder, verbose=False):
    """Evaluate model for a single recording."""
    from . import preprocess_dataset
    from . import features

    for target_folder in get_recognizer_folders(model_folder):
        # The source is later than the target. That means we need to
        # refresh the target
        if "preprocessed" in target_folder:
            logging.info("Start applying preprocessing methods...")
            t = target_folder
            _, _, preprocessing_queue = preprocess_dataset.get_parameters(t)
            handwriting = HandwrittenData.HandwrittenData(recording)
            if verbose:
                handwriting.show()
            handwriting.preprocessing(preprocessing_queue)
            if verbose:
                logging.debug("After preprocessing: %s",
                              handwriting.get_sorted_pointlist())
                handwriting.show()
        elif "feature-files" in target_folder:
            logging.info("Create feature file...")
            infofile_path = os.path.join(target_folder, "info.yml")
            with open(infofile_path, 'r') as ymlfile:
                feature_description = yaml.load(ymlfile)
            feature_str_list = feature_description['features']
            feature_list = features.get_features(feature_str_list)
            feature_count = sum(map(lambda n: n.get_dimension(),
                                    feature_list))
            x = handwriting.feature_extraction(feature_list)

            # Create pfile
            _, output_filename = tempfile.mkstemp(suffix='.pfile', text=True)
            create_pfile(output_filename, feature_count, [(x, 0)])
        elif "model" in target_folder:
            logfile, model_use = _evaluate_model_single_file(target_folder,
                                                             output_filename)
            return logfile
        else:
            logging.info("'%s' not found", target_folder)
    os.remove(output_filename)
    os.remove(model_use)


def get_index2latex(model_description):
    """Get a dictionary that maps indices to LaTeX commands.

    :param model_description: A model description file that points to
                              a feature folder where an
                              ``index2formula_id.csv`` has to be.
    :returns: Dictionary that maps indices to LaTeX commands
    """
    index2latex = {}
    translation_csv = os.path.join(get_project_root(),
                                   model_description["data-source"],
                                   "index2formula_id.csv")
    with open(translation_csv) as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in csvreader:
            index2latex[int(row['index'])] = row['latex']
    return index2latex


def classify_single_recording(raw_data_json, model_folder, verbose=False):
    """Get the classification as a list of tuples. The first value is the
       LaTeX code, the second value is the probability.
    """
    evaluation_file = evaluate_model(raw_data_json, model_folder, verbose)
    with open(os.path.join(model_folder, "info.yml")) as ymlfile:
        model_description = yaml.load(ymlfile)

    index2latex = get_index2latex(model_description)

    # Map line to probabilites for LaTeX commands
    with open(evaluation_file) as f:
        probabilities = f.read()
    probabilities = map(float, probabilities.split(" "))
    results = []
    for index, probability in enumerate(probabilities):
        results.append((index2latex[index], probability))
    results = sorted(results, key=lambda n: n[1], reverse=True)
    return results


def get_objectlist(description, config_key, module):
    """Take a description and return a list of classes.
    :param description: list of dictionaries, where each dictionary has only
                        one entry. The key is the name of a class.
                        The value of that entry is a list of
                        dictionaries again. Those dictionaries are paramters.
    :returns: List of objects."""
    object_list = []
    for feature in description:
        for feat, params in feature.items():
            feat = get_class(feat, config_key, module)
            if params is None:
                object_list.append(feat())
            else:
                parameters = {}
                for dicts in params:
                    for param_name, param_value in dicts.items():
                        parameters[param_name] = param_value
                object_list.append(feat(**parameters))  # pylint: disable=W0142
    return object_list


def get_class(name, config_key, module):
    """Get the class by its name as a string."""
    clsmembers = inspect.getmembers(module, inspect.isclass)
    for string_name, act_class in clsmembers:
        if string_name == name:
            return act_class

    # Check if the user has specified a plugin and if the class is in there
    cfg = get_project_configuration()
    if config_key in cfg:
        modname = os.path.splitext(os.path.basename(cfg[config_key]))[0]
        if os.path.isfile(cfg[config_key]):
            usermodule = imp.load_source(modname, cfg[config_key])
            clsmembers = inspect.getmembers(usermodule, inspect.isclass)
            for string_name, act_class in clsmembers:
                if string_name == name:
                    return act_class
        else:
            logging.warning("File '%s' does not exist. Adjust ~/.hwrtrc.",
                            cfg['data_analyzation_plugins'])

    logging.debug("Unknown class '%s'.", name)
    return None
