#!/usr/bin/env python
# -*- coding: utf-8 -*-

import nose


def crohme_get_parser_test():
    from hwrt.datasets import crohme_eval
    crohme_eval.get_parser()


def expressmatch_get_writemath_username_test():
    from hwrt.datasets import expressmatch
    path = '/home/moose/Downloads/expressmatch-time-datasetV0.2/65_Nina.inkml'
    expressmatch.get_writemath_username(path)


def inkml_normalize_symbol_name_test():
    from hwrt.datasets import inkml
    nose.tools.assert_equal(inkml.normalize_symbol_name('A'), 'A')


def mathbrush_mathbrush_formula_fix_test():
    from hwrt.datasets import mathbrush
    nose.tools.assert_equal(mathbrush.mathbrush_formula_fix('lparen'), '(')


def mfrdb_strip_end_test():
    from hwrt.datasets import mfrdb
    nose.tools.assert_equal(mfrdb.strip_end('asdf', 'df'), 'as')


def mfrdb_eval_less_than_test():
    from hwrt import utils
    utils.less_than([1, 2, 3], 2)


# def mfrdb_import_get_parser_test():
#     from hwrt.datasets import mfrdb_import
#     mfrdb_import.get_parser()


# def scg_ink_get_parser_test():
#     from hwrt.datasets import scg_ink
#     scg_ink.get_parser()
