#!/usr/bin/env python

"""Classify recordings."""

# Core Library modules
import logging
import os
from typing import Any, Dict, List, Optional

# Third party modules
import pkg_resources

# First party modules
from hwrt import utils

logger = logging.getLogger(__name__)
single_symbol_classifier = None


class SingleClassificer:
    """Classifier for single (and hence perfectly segmented) symbols."""

    def __init__(self):
        logger.info("Start reading model...")
        model_path = pkg_resources.resource_filename(__name__, "misc/")
        model_file = os.path.join(model_path, "model.tar")
        logger.info(f"Model: {model_file}")
        (preprocessing_queue, feature_list, model, output_semantics) = utils.load_model(
            model_file
        )
        self.preprocessing_queue = preprocessing_queue
        self.feature_list = feature_list
        self.model = model
        self.output_semantics_orig = output_semantics
        self.output_semantics = self.output_semantics_orig
        if "HWRT_ENV" in os.environ and os.environ["HWRT_ENV"] == "dev":
            new_semantics = []
            for el in output_semantics:
                new_semantics.append(el.split(";")[1])
            self.output_semantics = new_semantics

    def predict(
        self, recording: str, result_format: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Predict the class of the given recording.

        Parameters
        ----------
        recording : str
            Recording of a single handwritten dataset in JSON format.
        result_format : Optional[str]
            If it is 'LaTeX', then only the latex code will be returned

        Returns
        -------
        predictions : List[Dict]
        """
        evaluate = utils.evaluate_model_single_recording_preloaded
        results = evaluate(
            self.preprocessing_queue,
            self.feature_list,
            self.model,
            self.output_semantics,
            recording,
        )
        if result_format == "LaTeX":
            for i in range(len(results)):
                results[i]["semantics"] = results[i]["semantics"].split(";")[1]
        for i in range(len(results)):
            splitted = results[i]["semantics"].split(";")
            results[i]["complete_latex"] = splitted[1]
        return results


def classify_segmented_recording(recording, result_format=None) -> List[Dict[str, Any]]:
    """Use this function if you are sure you have a single symbol.

    Parameters
    ----------
    recording : string
        The recording in JSON format

    Returns
    -------
    predictions : List[Dict[str, Any]]
        Each dictionary contains the keys 'symbol' and 'probability'. The list
        is sorted descending by probability.
    """
    global single_symbol_classifier
    if single_symbol_classifier is None:
        single_symbol_classifier = SingleClassificer()
    return single_symbol_classifier.predict(recording, result_format)
