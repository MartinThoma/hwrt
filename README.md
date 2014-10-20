[![Build Status](https://travis-ci.org/MartinThoma/hwrt.svg?branch=master)](https://travis-ci.org/MartinThoma/hwrt)
[![Coverage Status](https://img.shields.io/coveralls/MartinThoma/hwrt.svg)](https://coveralls.io/r/MartinThoma/hwrt?branch=master)
[![Documentation Status](https://readthedocs.org/projects/hwrt/badge/?version=latest)](https://readthedocs.org/projects/hwrt/?badge=latest)

## Handwriting Recognition Toolkit

A toolkit for handwriting recognition. Especially on-line HWR.

### Version history

* 0.1 First uploads

### Installation

    sudo pip install hwrt

### Update

Currently, hwrt is under heavy development. That is very unlikely to change
before december 2014. To update it, simply run

    sudo pip install hwrt --upgrade


### For developers of hwrt

Update the project:

    python setup.py sdist upload

Coverage:

    nosetests --with-coverage --cover-erase --cover-package hwrt --logging-level=INFO --cover-html
    coveralls