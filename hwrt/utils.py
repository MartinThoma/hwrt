"""Utility functions that can be used in multiple scripts."""

# Core Library modules
import csv
import datetime
import importlib.machinery
import inspect
import json
import logging
import os
import pickle
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from decimal import Decimal, getcontext
from functools import reduce
from typing import Any, Dict, List, Optional, Type
from uuid import UUID

# Third party modules
import natsort
import numpy
import pkg_resources
import yaml

# Local modules
from . import handwritten_data

logger = logging.getLogger(__name__)
getcontext().prec = 100


def print_status(total, current, start_time=None):
    """
    Show how much work was done / how much work is remaining.

    Parameters
    ----------
    total : float
        The total amount of work
    current : float
        The work that has been done so far
    start_time : int
        The start time in seconds since 1970 to estimate the remaining time.
    """
    percentage_done = float(current) / total
    sys.stdout.write("\r%0.2f%% " % (percentage_done * 100))
    if start_time is not None:
        current_running_time = time.time() - start_time
        remaining_seconds = current_running_time / percentage_done
        tmp = datetime.timedelta(seconds=remaining_seconds)
        sys.stdout.write("(%s remaining)   " % str(tmp))
    sys.stdout.flush()


def get_project_configuration():
    """Get project configuration as dictionary."""
    home = os.path.expanduser("~")
    rcfile = os.path.join(home, ".hwrtrc")
    if not os.path.isfile(rcfile):
        create_project_configuration(rcfile)
    with open(rcfile) as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    return cfg


def create_project_configuration(filename):
    """Create a project configuration file which contains a configuration
    that might make sense."""
    home = os.path.expanduser("~")
    project_root_folder = os.path.join(home, "hwr-experiments")
    config = {
        "root": project_root_folder,
        "nntoolkit": None,
        "dropbox_app_key": None,
        "dropbox_app_secret": None,
        "dbconfig": os.path.join(home, "hwrt-config/db.config.yml"),
        "data_analyzation_queue": [{"Creator": None}],
        "worker_api_key": "1234567890abc",
        "environment": "development",
    }
    with open(filename, "w") as fp:
        yaml.dump(config, fp, default_flow_style=False)


def get_project_root():
    """Get the project root folder as a string."""
    cfg = get_project_configuration()
    # At this point it can be sure that the configuration file exists
    # Now make sure the project structure exists
    for dirname in [
        "raw-datasets",
        "preprocessed",
        "feature-files",
        "models",
        "reports",
    ]:
        directory = os.path.join(cfg["root"], dirname)
        if not os.path.exists(directory):
            os.makedirs(directory)

    raw_yml_path = pkg_resources.resource_filename(__name__, "misc/")

    # TODO: How to check for updates if it already exists?
    raw_data_dst = os.path.join(cfg["root"], "raw-datasets/info.yml")
    if not os.path.isfile(raw_data_dst):
        raw_yml_pkg_src = os.path.join(raw_yml_path, "info.yml")
        shutil.copy(raw_yml_pkg_src, raw_data_dst)

    # Make sure small-baseline folders exists
    for dirname in [
        "models/small-baseline",
        "feature-files/small-baseline",
        "preprocessed/small-baseline",
    ]:
        directory = os.path.join(cfg["root"], dirname)
        if not os.path.exists(directory):
            os.makedirs(directory)

    # Make sure small-baseline yml files exist
    paths = [
        ("preprocessed/small-baseline/", "preprocessing-small-info.yml"),
        ("feature-files/small-baseline/", "feature-small-info.yml"),
        ("models/small-baseline/", "model-small-info.yml"),
    ]
    for dest, src in paths:
        raw_data_dst = os.path.join(cfg["root"], "%s/info.yml" % dest)
        if not os.path.isfile(raw_data_dst):
            raw_yml_pkg_src = os.path.join(raw_yml_path, src)
            shutil.copy(raw_yml_pkg_src, raw_data_dst)

    return cfg["root"]


def get_template_folder():
    """Get path to the folder where th HTML templates are."""
    cfg = get_project_configuration()
    if "templates" not in cfg:
        home = os.path.expanduser("~")
        rcfile = os.path.join(home, ".hwrtrc")
        cfg["templates"] = pkg_resources.resource_filename("hwrt", "templates/")
        with open(rcfile, "w") as fp:
            yaml.dump(cfg, fp, default_flow_style=False)
    return cfg["templates"]


def get_nntoolkit() -> str:
    """Get the nntoolkit as a string."""
    cfg = get_project_configuration()
    return cfg["nntoolkit"]


def get_latest_in_folder(folder, ending="", default=""):
    """Get the file that comes last with natural sorting in folder and has
    file ending 'ending'.
    """
    latest = default
    for my_file in natsort.natsorted(os.listdir(folder), reverse=True):
        if my_file.endswith(ending):
            latest = os.path.join(folder, my_file)
            return latest
    return latest


def get_latest_folder(folder):
    """Get the absolute path of a subfolder that comes last with natural
    sorting in the given folder.
    """
    folders = [
        os.path.join(folder, name)
        for name in os.listdir(folder)
        if os.path.isdir(os.path.join(folder, name))
    ]
    folders = natsort.natsorted(folders, reverse=True)
    if len(folders) == 0:
        # No model folder!
        logger.error(
            "You don't have any model folder. I suggest you "
            "have a look at "
            "https://github.com/MartinThoma/hwr-experiments and "
            "http://pythonhosted.org/hwrt/"
        )
        sys.exit(-1)
    else:
        return os.path.abspath(folders[0])


def get_database_config_file():
    """Get the absolute path to the database configuration file."""
    cfg = get_project_configuration()
    if "dbconfig" in cfg:
        if os.path.isfile(cfg["dbconfig"]):
            return cfg["dbconfig"]
        else:
            logger.info(
                f"File '{cfg['dbconfig']}' was not found. Adjust 'dbconfig' "
                f"in your "
                "~/.hwrtrc file."
            )
    else:
        logger.info(
            "No database connection file found. "
            "Specify 'dbconfig' in your ~/.hwrtrc file."
        )
    return None


def get_database_configuration() -> Optional[Dict]:
    """Get database configuration as dictionary."""
    db_config = get_database_config_file()
    if db_config is None:
        return None
    with open(db_config) as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    return cfg


def sizeof_fmt(num):
    """Takes the a filesize in bytes and returns a nicely formatted string. """
    for x in ["bytes", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            return f"{num:3.1f} {x}"
        num /= 1024.0


def input_int_default(question="", default=0):
    """A function that works for both, Python 2.x and Python 3.x.
    It asks the user for input and returns it as a string.
    """
    answer = input(question)
    if answer in ["", "yes"]:
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
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
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
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


def get_latest_model(model_folder, basename):
    """Get the latest model (determined by the name of the model in
    natural sorted order) which begins with `basename`."""
    models = [n for n in os.listdir(model_folder) if n.endswith(".json")]
    models = [n for n in models if n.startswith(basename)]
    models = natsort.natsorted(models, reverse=True)
    if len(models) == 0:
        return None
    else:
        return os.path.join(model_folder, models[0])


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


def get_latest_successful_run(folder: str) -> Optional[datetime.datetime]:
    """Get the latest successful run timestamp."""
    runfile = os.path.join(folder, "run.log")
    if not os.path.isfile(runfile):
        return None
    with open(runfile) as fp:
        content = fp.readlines()
    return datetime.datetime.strptime(content[0], "timestamp: '%Y-%m-%d %H:%M:%S'")


def create_run_logfile(folder: str) -> None:
    """Create a 'run.log' within folder. This file contains the time of the
    latest successful run.
    """
    with open(os.path.join(folder, "run.log"), "w") as fp:
        datestring = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        fp.write("timestamp: '%s'" % datestring)


def choose_raw_dataset(currently: str = ""):
    """Let the user choose a raw dataset. Return the absolute path."""
    folder = os.path.join(get_project_root(), "raw-datasets")
    files = [
        os.path.join(folder, name)
        for name in os.listdir(folder)
        if name.endswith(".pickle")
    ]
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


def get_readable_time(duration: int) -> str:
    """
    Format the time to a readable format.

    Parameters
    ----------
    duration : int
        Time in ms

    Returns
    -------
    string
        The time splitted to highest used time (minutes, hours, ...)
    """
    ms = duration % 1000
    duration -= ms
    duration //= 1000

    sec = duration % 60
    duration -= sec
    duration //= 60

    minutes = duration % 60
    duration -= minutes
    duration //= 60

    if duration != 0:
        return "%ih, %i minutes %is %ims" % (duration, minutes, sec, ms)
    elif minutes != 0:
        return "%i minutes %is %ims" % (minutes, sec, ms)
    elif sec != 0:
        return "%is %ims" % (sec, ms)
    else:
        return "%ims" % ms


def default_model():
    """Get a path for a default value for the model. Start searching in the
    current directory."""
    project_root = get_project_root()
    models_dir = os.path.join(project_root, "models")
    curr_dir = os.getcwd()
    if (
        os.path.commonprefix([models_dir, curr_dir]) == models_dir
        and curr_dir != models_dir
    ):
        latest_model = curr_dir
    else:
        latest_model = get_latest_folder(models_dir)
    return latest_model


def create_adjusted_model_for_percentages(model_src, model_use):
    """Replace logreg layer by sigmoid to get probabilities."""
    # Copy model file
    shutil.copyfile(model_src, model_use)
    # Adjust model file
    with open(model_src) as fp:
        content = fp.read()
    content = content.replace("logreg", "sigmoid")
    with open(model_use, "w") as fp:
        fp.write(content)


def create_hdf5(output_filename, feature_count, data):
    """
    Create a HDF5 feature files.

    Parameters
    ----------
    output_filename : string
        name of the HDF5 file that will be created
    feature_count : int
        dimension of all features combined
    data : list of tuples
        list of (x, y) tuples, where x is the feature vector of dimension
        ``feature_count`` and y is a label.
    """
    # Third party modules
    import h5py

    logger.info(f"Start creating of {output_filename} hdf file")
    x = []
    y = []
    for features, label in data:
        assert (
            len(features) == feature_count
        ), "Expected %i features, got %i features" % (feature_count, len(features))
        x.append(features)
        y.append(int(label))
    wfile = h5py.File(output_filename, "w")
    wfile.create_dataset("data", data=x, dtype="float32")
    wfile.create_dataset("labels", data=y, dtype="int32")
    wfile.close()


def get_recognizer_folders(model_folder):
    """Get a list of folders [preprocessed, feature-files, model]."""
    folders = []
    folder = model_folder
    while os.path.isdir(folder):
        folders.append(folder)
        # Get info.yml
        with open(os.path.join(folder, "info.yml")) as ymlfile:
            content = yaml.safe_load(ymlfile)
        folder = os.path.join(get_project_root(), content["data-source"])
    return folders[::-1]  # Reverse order to get the most "basic one first"


def load_model(model_file):
    """Load a model by its file. This includes the model itself, but also
    the preprocessing queue, the feature list and the output semantics.
    """
    # Extract tar
    with tarfile.open(model_file) as tar:
        tarfolder = tempfile.mkdtemp()
        tar.extractall(path=tarfolder)

    # Local modules
    from . import features, preprocessing

    # Get the preprocessing
    with open(os.path.join(tarfolder, "preprocessing.yml")) as ymlfile:
        preprocessing_description = yaml.safe_load(ymlfile)
    preprocessing_queue = preprocessing.get_preprocessing_queue(
        preprocessing_description["queue"]
    )

    # Get the features
    with open(os.path.join(tarfolder, "features.yml")) as ymlfile:
        feature_description = yaml.safe_load(ymlfile)
    feature_str_list = feature_description["features"]
    feature_list = features.get_features(feature_str_list)

    # Get the model
    # Third party modules
    import nntoolkit.utils

    model = nntoolkit.utils.get_model(model_file)

    output_semantics_file = os.path.join(tarfolder, "output_semantics.csv")
    output_semantics = nntoolkit.utils.get_outputs(output_semantics_file)

    # Cleanup
    shutil.rmtree(tarfolder)

    return (preprocessing_queue, feature_list, model, output_semantics)


def evaluate_model_single_recording_preloaded(
    preprocessing_queue,
    feature_list,
    model,
    output_semantics,
    recording,
    recording_id=None,
):
    """
    Evaluate a model for a single recording, after everything has been loaded.

    Parameters
    ----------
    preprocessing_queue : list
        List of all preprocessing objects.
    feature_list : list
        List of all feature objects.
    model : dict
        Neural network model.
    output_semantics : list
        List that defines what an output means.
    recording : string in JSON format
        The handwritten recording in JSON format.
    recording_id : int or None
        For debugging purposes.
    """
    handwriting = handwritten_data.HandwrittenData(recording, raw_data_id=recording_id)
    handwriting.preprocessing(preprocessing_queue)
    x = handwriting.feature_extraction(feature_list)
    # Third party modules
    import nntoolkit.evaluate

    model_output = nntoolkit.evaluate.get_model_output(model, [x])
    return nntoolkit.evaluate.get_results(model_output, output_semantics)


def get_possible_splits(n):
    """
    Parameters
    ----------
    n : int
        n strokes were make
    """
    get_bin = (
        lambda x, n: x >= 0
        and str(bin(x))[2:].zfill(n)
        or "-" + str(bin(x))[3:].zfill(n)
    )
    possible_splits = []
    for i in range(2 ** (n - 1)):
        possible_splits.append(get_bin(i, n - 1))
    return possible_splits


def segment_by_split(split, recording):
    """

    Parameters
    ----------
    split : String of 0s and 1s
        For example "010".
    recording : list
        A recording of handwritten text.
    """
    segmented = [[recording[0]]]
    for i in range(len(recording) - 1):
        if split[i] == "1":
            segmented.append([])
        segmented[-1].append(recording[i + 1])
    assert split.count("1") + 1 == len(segmented), (
        f'split.count("1") + 1 = {split.count("1") + 1} != '
        f"{len(segmented)} = len(segmented)"
    )
    return segmented


def evaluate_model_single_recording_preloaded_multisymbol(
    preprocessing_queue, feature_list, model, output_semantics, recording
):
    """
    Evaluate a model for a single recording, after everything has been loaded.
    Multiple symbols are recognized.

    Parameters
    ----------
    preprocessing_queue : list
        List of all preprocessing objects.
    feature_list : list
        List of all feature objects.
    model : dict
        Neural network model.
    output_semantics :
        List that defines what an output means.
    recording :
        The handwritten recording in JSON format.
    """
    # Third party modules
    import nntoolkit.evaluate

    recording = json.loads(recording)
    logger.info(f"## start ({len(recording)} strokes)" + "#" * 80)
    hypotheses = []  # [[{'score': 0.123, symbols: [123, 123]}]  # split0
    #  []] # Split i...
    for split in get_possible_splits(len(recording)):
        recording_segmented = segment_by_split(split, recording)
        cur_split_results = []
        for symbol in recording_segmented:
            handwriting = handwritten_data.HandwrittenData(json.dumps(symbol))
            handwriting.preprocessing(preprocessing_queue)
            x = handwriting.feature_extraction(feature_list)

            model_output = nntoolkit.evaluate.get_model_output(model, [x])
            results = nntoolkit.evaluate.get_results(model_output, output_semantics)
            results = results[:10]
            cur_split_results.append(
                [el for el in results if el["probability"] >= 0.01]
            )

        # Now that I have all symbols of this split, I have to get all
        # combinations of the hypothesis
        # Core Library modules
        import itertools

        for hyp in itertools.product(*cur_split_results):
            hypotheses.append(
                {
                    "score": reduce(lambda x, y: x * y, [s["probability"] for s in hyp])
                    * len(hyp)
                    / len(recording),
                    "symbols": [s["semantics"] for s in hyp],
                    "min_part": min(s["probability"] for s in hyp),
                    "segmentation": split,
                }
            )

    hypotheses = sorted(hypotheses, key=lambda n: n["min_part"], reverse=True)[:10]
    for _i, hyp in enumerate(hypotheses):
        if hyp["score"] > 0.001:
            logger.info(
                "%0.4f: %s (seg: %s)", hyp["score"], hyp["symbols"], hyp["segmentation"]
            )
    return nntoolkit.evaluate.get_results(model_output, output_semantics)


def evaluate_model_single_recording_multisymbol(model_file, recording):
    """
    Evaluate a model for a single recording where possibly multiple symbols
    are.

    Parameters
    ----------
    model_file : string
        Model file (.tar)
    recording :
        The handwritten recording.
    """
    (preprocessing_queue, feature_list, model, output_semantics) = load_model(
        model_file
    )
    logger.info("multiple symbol mode")
    logger.info(recording)
    results = evaluate_model_single_recording_preloaded(
        preprocessing_queue, feature_list, model, output_semantics, recording
    )
    return results


def evaluate_model_single_recording(model_file, recording):
    """
    Evaluate a model for a single recording.

    Parameters
    ----------
    model_file : string
        Model file (.tar)
    recording :
        The handwritten recording.
    """
    (preprocessing_queue, feature_list, model, output_semantics) = load_model(
        model_file
    )
    results = evaluate_model_single_recording_preloaded(
        preprocessing_queue, feature_list, model, output_semantics, recording
    )
    return results


def _evaluate_model_single_file(target_folder, test_file):
    """
    Evaluate a model for a single recording.

    Parameters
    ----------
    target_folder : string
        Folder where the model is
    test_file : string
        The test file (.hdf5)
    """
    logger.info("Create running model...")
    model_src = get_latest_model(target_folder, "model")
    model_file_pointer = tempfile.NamedTemporaryFile(delete=False)
    model_use = model_file_pointer.name
    model_file_pointer.close()
    logger.info(f"Adjusted model is in {model_use}.")
    create_adjusted_model_for_percentages(model_src, model_use)

    # Run evaluation
    project_root = get_project_root()
    time_prefix = time.strftime("%Y-%m-%d-%H-%M")
    logger.info(f"Evaluate '{model_src}' with '{test_file}'...")
    logfilefolder = os.path.join(project_root, "logs/")
    if not os.path.exists(logfilefolder):
        os.makedirs(logfilefolder)
    logfile = os.path.join(project_root, "logs/%s-error-evaluation.log" % time_prefix)
    with open(logfile, "w") as log, open(model_use) as modl_src_p:
        p = subprocess.Popen(
            [get_nntoolkit(), "run", "--batch-size", "1", "-f%0.4f", test_file],
            stdin=modl_src_p,
            stdout=log,
        )
        ret = p.wait()
        if ret != 0:
            logger.error(f"nntoolkit finished with ret code {ret}")
            sys.exit()
    return (logfile, model_use)


def evaluate_model(recording, model_folder, verbose=False):
    """Evaluate model for a single recording."""
    # Local modules
    from . import features, preprocess_dataset

    for target_folder in get_recognizer_folders(model_folder):
        # The source is later than the target. That means we need to
        # refresh the target
        if "preprocessed" in target_folder:
            logger.info("Start applying preprocessing methods...")
            t = target_folder
            _, _, preprocessing_queue = preprocess_dataset.get_parameters(t)
            handwriting = handwritten_data.HandwrittenData(recording)
            if verbose:
                handwriting.show()
            handwriting.preprocessing(preprocessing_queue)
            if verbose:
                logger.debug(
                    "After preprocessing: %s", handwriting.get_sorted_pointlist()
                )
                handwriting.show()
        elif "feature-files" in target_folder:
            logger.info("Create feature file...")
            infofile_path = os.path.join(target_folder, "info.yml")
            with open(infofile_path) as ymlfile:
                feature_description = yaml.safe_load(ymlfile)
            feature_str_list = feature_description["features"]
            feature_list = features.get_features(feature_str_list)
            feature_count = sum(n.get_dimension() for n in feature_list)
            x = handwriting.feature_extraction(feature_list)

            # Create hdf5
            _, output_filename = tempfile.mkstemp(suffix=".hdf5", text=True)
            create_hdf5(output_filename, feature_count, [(x, 0)])
        elif "model" in target_folder:
            logfile, model_use = _evaluate_model_single_file(
                target_folder, output_filename
            )
            return logfile
        else:
            logger.info("'%s' not found", target_folder)
    os.remove(output_filename)
    os.remove(model_use)


def get_index2latex(model_description):
    """
    Get a dictionary that maps indices to LaTeX commands.

    Parameters
    ----------
    model_description : string
        A model description file that points to a feature folder where an
        `index2formula_id.csv` has to be.

    Returns
    -------
    dictionary :
        Maps indices to LaTeX commands
    """
    index2latex = {}
    translation_csv = os.path.join(
        get_project_root(), model_description["data-source"], "index2formula_id.csv"
    )
    with open(translation_csv) as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=",", quotechar='"')
        for row in csvreader:
            index2latex[int(row["index"])] = row["latex"]
    return index2latex


def get_index2data(model_description):
    """
    Get a dictionary that maps indices to a list of (1) the id in the
    hwrt symbol database (2) the latex command (3) the unicode code point
    (4) a font family and (5) a font style.

    Parameters
    ----------
    model_description : string
        A model description file that points to a feature folder where an
        ``index2formula_id.csv`` has to be.

    Returns
    -------
    dictionary
        that maps indices to lists of data

    Notes
    -----
    This command need a database connection.
    """
    index2latex = {}
    translation_csv = os.path.join(
        get_project_root(), model_description["data-source"], "index2formula_id.csv"
    )
    with open(translation_csv) as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=",", quotechar='"')
        for row in csvreader:
            database_id = int(row["formula_id"])
            online_data = get_online_symbol_data(database_id)
            latex = online_data["formula_in_latex"]
            unicode_code_point = online_data["unicode_dec"]
            font = online_data["font"]
            font_style = online_data["font_style"]
            index2latex[int(row["index"])] = [
                database_id,
                latex,
                unicode_code_point,
                font,
                font_style,
            ]
    return index2latex


def get_online_symbol_data(database_id):
    """Get from the server."""
    # Third party modules
    import pymysql
    import pymysql.cursors

    cfg = get_database_configuration()
    mysql = cfg["mysql_online"]
    connection = pymysql.connect(
        host=mysql["host"],
        user=mysql["user"],
        passwd=mysql["passwd"],
        db=mysql["db"],
        cursorclass=pymysql.cursors.DictCursor,
    )
    cursor = connection.cursor()
    sql = (
        "SELECT `id`, `formula_in_latex`, `unicode_dec`, `font`, "
        "`font_style` FROM  `wm_formula` WHERE  `id` =%i"
    ) % database_id
    cursor.execute(sql)
    datasets = cursor.fetchall()
    if len(datasets) == 1:
        return datasets[0]
    return None


def classify_single_recording(raw_data_json, model_folder, verbose=False):
    """
    Get the classification as a list of tuples. The first value is the LaTeX
    code, the second value is the probability.
    """
    evaluation_file = evaluate_model(raw_data_json, model_folder, verbose)
    with open(os.path.join(model_folder, "info.yml")) as ymlfile:
        model_description = yaml.safe_load(ymlfile)

    index2latex = get_index2latex(model_description)

    # Map line to probabilites for LaTeX commands
    with open(evaluation_file) as fp:
        probabilities = fp.read()
    probabilities = list(map(float, probabilities.split(" ")))
    results = []
    for index, probability in enumerate(probabilities):
        results.append((index2latex[index], probability))
    results = sorted(results, key=lambda n: n[1], reverse=True)
    return results


def get_objectlist(
    description: List[Dict[str, Any]], config_key: str, module
) -> List[Any]:
    """
    Take a description and return a list of classes.

    Parameters
    ----------
    description : List[Dict[str, Any]]
        Each dictionary has only one entry. The key is the name of a class. The
        value of that entry is a list of dictionaries again. Those dictionaries
        are paramters.

    Returns
    -------
    object_list : List[Any]
    """
    object_list = []
    for feature in description:
        for feat_name, params in feature.items():
            feat = get_class(feat_name, config_key, module)
            if params is None:
                object_list.append(feat())
            else:
                parameters = {}
                for dicts in params:
                    for param_name, param_value in dicts.items():
                        parameters[param_name] = param_value
                object_list.append(feat(**parameters))  # pylint: disable=W0142
    return object_list


def get_class(name, config_key, module) -> Type:
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
            usermodule = importlib.machinery.SourceFileLoader(
                modname, cfg[config_key]
            ).load_module(modname)
            clsmembers = inspect.getmembers(usermodule, inspect.isclass)
            for string_name, act_class in clsmembers:
                if string_name == name:
                    return act_class
        else:
            logger.warning(
                "File '%s' does not exist. Adjust ~/.hwrtrc.",
                cfg["data_analyzation_plugins"],
            )

    raise ValueError(f"Class '{name}' is unknown")


def less_than(list_: List[float], n: int) -> float:
    """
    Get number of symbols in `list_` which have a value less than `n`.

    Parameters
    ----------
    list_ : List[float]
    n : int

    Returns
    -------
    float :
        Number of elements of the list_ which are strictly less than n.
    """
    return float(len([1 for el in list_ if el < n]))


def get_mysql_cfg():
    """
    Get the appropriate MySQL configuration
    """
    environment = get_project_configuration()["environment"]
    cfg = get_database_configuration()
    if environment == "production":
        mysql = cfg["mysql_online"]
    else:
        mysql = cfg["mysql_dev"]
    return mysql


def softmax(w: List[float], t: float = 1.0) -> List[float]:
    """
    Calculate the softmax of a list of numbers w.

    Parameters
    ----------
    w : List[float]
    t : float
        The temperature

    Returns
    -------
    result : List[float]
        a list of the same length as w of non-negative numbers

    Examples
    --------
    >>> ["{:.8f}".format(el) for el in softmax([0.1, 0.2])]
    ['0.47502081', '0.52497919']
    >>> ["{:.8f}".format(el) for el in softmax([-0.1, 0.2])]
    ['0.42555748', '0.57444252']
    >>> ["{:.8f}".format(el) for el in softmax([0.9, -10])]
    ['0.99998154', '0.00001846']
    >>> ["{:.8f}".format(el) for el in softmax([0, 10])]
    ['0.00004540', '0.99995460']
    """  # noqa
    w_tmp = [Decimal(el) for el in w]
    exp = numpy.exp(numpy.array(w_tmp) / Decimal(t))
    dist = exp / numpy.sum(exp)
    return dist


def get_beam_cache_directory():
    """
    Get a directory where pickled Beam Data can be stored.

    Create that directory, if it doesn't exist.

    Returns
    -------
    str
        Path to the directory
    """
    home = os.path.expanduser("~")
    cache_dir = os.path.join(home, ".hwrt-beam-cache")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    return cache_dir


def get_beam(secret_uuid):
    """
    Get a beam from the session with `secret_uuid`.

    Parameters
    ----------
    secret_uuid : str

    Returns
    -------
    The beam object if it exists, otherwise `None`.
    """
    beam_dir = get_beam_cache_directory()
    beam_filename = os.path.join(beam_dir, secret_uuid)
    if os.path.isfile(beam_filename):
        with open(beam_filename, "rb") as handle:
            beam = pickle.load(handle)
        return beam
    return None


def store_beam(beam, secret_uuid: str) -> None:
    """Save the beam to a pickle file."""
    beam_dir = get_beam_cache_directory()
    beam_filename = os.path.join(beam_dir, secret_uuid)
    with open(beam_filename, "wb") as pfile:
        pickle.dump(beam, pfile, protocol=pickle.HIGHEST_PROTOCOL)


def is_valid_uuid(uuid_to_test: str, version: int = 4) -> bool:
    """
    Check if uuid_to_test is a valid UUID.

    Parameters
    ----------
    uuid_to_test : str
    version : {1, 2, 3, 4}

    Returns
    -------
    `True` if uuid_to_test is a valid UUID, otherwise `False`.

    Examples
    --------
    >>> is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
    True
    >>> is_valid_uuid('c9bf9e58')
    False
    """
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False

    return str(uuid_obj) == uuid_to_test


def get_symbols_filepath(testing: bool = False) -> str:
    """Get the filepath of the symbols YAML file."""
    pkg_root = os.path.dirname(sys.modules[__package__].__file__)
    if testing:
        symbol_yml_file = os.path.join(pkg_root, "./misc/symbols_tiny.yml")
    else:
        symbol_yml_file = os.path.join(pkg_root, "./misc/symbols.yml")
    return symbol_yml_file
