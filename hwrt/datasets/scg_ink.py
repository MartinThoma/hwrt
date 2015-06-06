#!/usr/bin/env python

"""Support for the SCG INK format defined in
https://www.scg.uwaterloo.ca/mathbrush/publications/corpus.pdf
"""


def write_hw_scgink(hw, filename='mathbrush-test.txt'):
    """
    Parameters
    ----------
    hw : HandwrittenData object
    filename : string
        Path, where the SCG INK file gets written
    """
    with open(filename, 'w') as f:
        f.write('SCG_INK\n')
        f.write('%i\n' % len(hw.get_pointlist()))
        for stroke in hw.get_pointlist():
            f.write('%i\n' % len(stroke))
            for point in stroke:
                f.write('%i %i\n' % (point['x'], point['y']))
