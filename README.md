[![Build Status](https://travis-ci.org/MartinThoma/hwrt.svg?branch=master)](https://travis-ci.org/MartinThoma/hwrt)
[![Coverage Status](https://img.shields.io/coveralls/MartinThoma/hwrt.svg)](https://coveralls.io/r/MartinThoma/hwrt?branch=master)
[![Documentation Status](https://readthedocs.org/projects/hwrt/badge/?version=latest)](https://readthedocs.org/projects/hwrt/?badge=latest)

## Handwriting Recognition Toolkit

A toolkit for handwriting recognition (HWR). Especially on-line HWR. It
was developed for the bachelor's thesis of Martin Thoma.

### Version history

* 0.1 First uploads

### Installation

You can install the handwriting recognition toolkit directly via pip:

    # pip install hwrt

If that doesn't work, you should consult the
[documentation](http://hwrt.readthedocs.org/).

### Update

Currently, hwrt is under heavy development. That is very unlikely to change
before december 2014. To update it, simply run

    # pip install hwrt --upgrade


### For developers of hwrt

Update the project:

    $ python setup.py sdist upload

Coverage:

    $ nosetests --with-coverage --cover-erase --cover-package hwrt --logging-level=INFO --cover-html
    $ coveralls

Code smug: `pylint`