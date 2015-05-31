Development
===========

The ``hwrt`` toolkit is developed by Martin Thoma. The development began in
May 2014.

It is developed on GitHub: https://github.com/MartinThoma/hwrt

You can file issues and feature requests there. Alternatively, you can send
me an email: info@martin-thoma.de

Contributions
-------------

Everybody is welcome to contribute to ``hwrt``. You can do so by

* Testing it and giving me feedback / opening issues on GitHub.

  * Writing unittests.

  * Simply using the software.

* Writing new code and sending it to me as pull requests or as email
  (info@martin-thoma.de). However, before you add new functionality you should
  eventually ask if I really want that in the project.

* Improving existing code.

  * Improving the front-end (HTML+CSS+JavaScript)

* Suggesting something else how you can contribute.


I suggest reading the issues page https://github.com/MartinThoma/hwrt/issues
for more ideas how you can contribute.


Tools
-----

* ``nosetests`` for unit testing
* ``pylint`` to find code smug
* GitHub for hosting the source code
* http://hwrt.readthedocs.org/ or https://pythonhosted.org/hwrt for hosting the documentation


Code coverage can be tested with

.. code:: bash

    $ nosetests --with-coverage --cover-erase --cover-package hwrt --logging-level=INFO --cover-html

and uploaded to coveralls.io with

.. code:: bash

    $ coveralls


Documentation
-------------

The documentation is generated with `Sphinx <http://sphinx-doc.org/latest/index.html>`_.
On Debian derivates it can be installed with

.. code:: bash

    $ sudo apt-get install python-sphinx
    $ sudo -H pip install numpydoc

Sphinx makes use of `reStructured Text <http://openalea.gforge.inria.fr/doc/openalea/doc/_build/html/source/sphinx/rest_syntax.html>`_

The documentation can be built with ``make html``.

The documentation is written in numpydoc syntax. Information about numpydoc
can be found at the `numpydoc repository <https://github.com/numpy/numpydoc>`_,
especially `A Guide to NumPy/SciPy Documentation <https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt>`_.



Project structure
-----------------

The project structure is

::

    .
    ├── bin
    ├── docs
    ├── hwrt
    │   ├── misc
    │   └── templates
    └── tests
        └── symbols


where the folder ``bin`` contains all scripts that can directly be used,
``hwrt`` contains all modules and ``tests`` contains unittests written with
nosetools.

The symbols subfolder contains JSON files of recordings that are used for
testing.


Current State
-------------

* lines of code without tests: LOC
* lines of test code: LOT
* test coverage: cov
* pylint score: lint

::

    date,        LOC,  LOT, cov, lint, cheesecake_index, users, changes
    2014-11-16, 3361,  936, 72%, 9.70, 314/595, 1
    2014-11-17, 3332,  965, 72%, 9.70, 314/595, 1, moved 'view.py' to subcommand 'hwrt view'
    2014-11-18, 3325,  988, 71%, 9.71, 314/595, 1, moved 'download.py' to subcommand 'hwrt download'
    2014-11-19, 3312,  988, 72%, 9.71, 314/595, 1, refactoring
    2014-11-20, 3281, 1001, 72%, 9.78, 314/595, 1, refactoring (logging); added test case for create_pfiles
    2014-11-21, 3274, 1001, 72%, 9.78, 314/595, 1, refactoring (temporary file)
    2014-11-22, 3282, 1001, 72%, 9.82, 315/595, 1, refactoring (temporary file for evaluation, fixed issue #7)
    2014-11-23, 3279, 1043, 72%, 9.83, 315/595, 1, moved 'analyze_data.py' to subcommand 'hwrt analyze_data'; refactoring (analyze_data.py)
    2014-11-24, 3286, 1069, 73%, 9.83, 315/595, 1, hwrt/utils.py: refactoring (tempfile; splitted long function)
    2014-11-25, 3445, 1070, 73%, 9.80, 314/595, 1, hwrt/data_analyzation_metrics.py: added AnalyzeErrors
    2014-11-26, 3455, 1136, 74%, 9.81, 315/595, 1, hwrt/create_pfiles.py: refactoring, normalization can get activated
    2014-11-27, 3450, 1140, 75%, 9.82, 315/595, 1, hwrt/view.py: refactoring; added test
    2014-11-28, 3443, 1149, 75%, 9.82, 315/595, 1, hwrt/data_analyzation_metrics.py: refactoring to simplify code; added images of rotated recording
    2014-11-29, 3448, 1147, 76%, 9.82, 315/595, 1, bin/test.py: refactored to use temporary file
    2014-11-30, 3464, 1165, 76%, 9.82, 315/595, 1, hwrt/create_pfiles.py: refactoring for easier testing
    2014-12-01, 3488, 1165, 76%, 9.82, 315/595, 1, bin/recordflask.py: Added web server draft
    2014-12-02, 3507, 1165, 76%, 9.82, 315/595, 1, bin/recordflask.py: Updated web server
    2014-12-03, 3525, 1165, 76%, 9.78, 316/595, 1, hwrt/utils.py: check configuration file for nntoolkit; formulas can now be recorded and evaluated without non-free software :-)
    2014-12-04, 3640, 1165, 76%, 9.75, 315/595, 1, hwrt/record.py and hwrt/serve.py: Improved recognizer; added model file to project
    2014-12-05, 3669, 1191, 76%, 9.79, 316/595, 1, updated code to work with Python 3
    2014-12-07, 3674, 1191, 76%, 9.80, 316/595, 1, Python 2.7; 3.3; 3.4 compatbility; added missing packages
    2014-12-08, 3689, 1191, 75%, 9.81, 317/595, 1, hwrt/selfcheck.py: Added possibility to see templates folder; improved templates
    2014-12-09, 3723, 1191, 75%, 9.79, 317/595, 1, hwrt/serve.py: Preload model
    2014-12-10, 3754, 1191, 75%, 9.78, 317/595, 1, bin/backup.py: Added possibility to get renderings from server; hwrt/serve.py: Added command line argument to adjust number of showed symbols and use MathJax to display them
    2014-12-11, 3741, 1211, 75%, 9.79, 317/595, 1, hwrt/analyze_data.py and hwrt/record.py: removed logging.basicConfig; added tests for record.py
    2014-12-12, 3798, 1211, 75%, 9.76, 317/595, 1, hwrt/serve.py: classify data on write-math.com
    2014-12-14, 3802, 1235, 74%, 9.77, 317/595, 1, minor adjustments
    2014-12-15, 3807, 1268, 76%, 9.78, 396/595, 1, hwrt/serve.py: catch problem if no internet connection; updated some docstrings
    2014-12-16, 3738, 1243, 76%, 9.80, 396/595, 1, hwrt/record.py: removed as the functionality is also in hwrt/serve.py
    2014-12-16, 3738, 1047, 76%, 9.80, 396/595, 1, tests: factored test helpers out in their own module
    2014-12-17, 3737, 1049, 76%, 9.80, 395/595, 1, code beautification: self.__repr__() -> repr(self); with open
    2014-12-18, 3721, 1086, 77%, 9.80, 395/595, 1, hwrt/features.py: More testing; abc baseclass
    2014-12-19, 3721, 1085, 77%, 9.80, 395/595, 1, hwrt/HandwrittenData.py: test show() method; removed unnecessary lines
    2015-04-13, 5999, 1085, 73%, 9.55, 443/595, 1, many updates
    2015-05-31, 6481, 1085, 71%, 8.97, 415/595, 1, many updates