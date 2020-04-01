#!/usr/bin/env python


def test_crohme_get_parser_test():
    from hwrt.datasets import crohme_eval

    crohme_eval.get_parser()


def test_expressmatch_get_writemath_username_test():
    from hwrt.datasets import expressmatch

    path = "/home/moose/Downloads/expressmatch-time-datasetV0.2/65_Nina.inkml"
    expressmatch.get_writemath_username(path)


def test_inkml_normalize_symbol_name_test():
    from hwrt.datasets import inkml

    assert inkml.normalize_symbol_name("A") == "A"


def test_mathbrush_mathbrush_formula_fix_test():
    from hwrt.datasets import mathbrush

    assert mathbrush.mathbrush_formula_fix("lparen") == "("


def test_mfrdb_strip_end_test():
    from hwrt.datasets import mfrdb

    assert mfrdb.strip_end("asdf", "df") == "as"


def test_mfrdb_eval_less_than_test():
    from hwrt import utils

    utils.less_than([1, 2, 3], 2)
