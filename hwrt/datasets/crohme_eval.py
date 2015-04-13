#!/usr/bin/env python

"""Evaluate a folder of InkML files for a CROHME competition."""

import glob


def evaluate_dir(sample_dir):
    """Evaluate all recordings in `sample_dir`.

    Parameters
    ----------
    sample_dir : string
        The path to a directory with *.inkml files.

    Returns
    -------
    list of dictionaries
        Each dictionary contains the keys 'filename' and 'results', where
        'results' itself is a list of dictionaries. Each of the results has
        the keys 'latex' and 'probability'
    """
    if sample_dir[-1] == "/":
        sample_dir = sample_dir[:-1]
    for filename in glob.glob("%s/*.inkml" % sample_dir):
        print(filename)
    # TODO
    return []


def evaluate_inkml(inkml_file_path):
    """Evaluate an InkML file.

    Parameters
    ----------
    TODO
    """
    # TODO
    return []


def generate_output_csv(evaluation_results, filename='results.csv'):
    """Generate the evaluation results in the format

    Parameters
    ----------
    evaluation_results : list of dictionaries
        Each dictionary contains the keys 'filename' and 'results', where
        'results' itself is a list of dictionaries. Each of the results has
        the keys 'latex' and 'probability'

    Examples
    --------
    MfrDB3907_85801, a, b, c, d, e, f, g, h, i, j
    scores, 1, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1
    MfrDB3907_85802, 1, |, l, COMMA, junk, x, X, \times
    scores, 10, 8.001, 2, 0.5, 0.1, 0,-0.5, -1, -100
    """
    with open(filename, 'w') as f:
        for result in evaluation_results:
            for i, entry in enumerate(result['results']):
                if entry['latex'] == ',':
                    result['results']['latex'] = 'COMMA'
            f.write("%s, " % result['filename'])
            f.write(", ".join([entry['latex'] for entry in result['results']]))
            f.write("\n")
            f.write("%s, " % "scores")
            f.write(", ".join([entry['latex'] for entry in result['results']]))
            f.write("\n")


def get_parser():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--dir",
                        dest="sample_dir",
                        help="directory with data to evaluate",
                        required=True,
                        metavar="DIRECTORY")
    return parser


def main(sample_dir):
    evaluation_results = evaluate_dir(sample_dir)
    generate_output_csv(evaluation_results)


if __name__ == "__main__":
    args = get_parser().parse_args()
    main(args.sample_dir)
