Development
===========

The ``hwrt`` toolkit is developed by Martin Thoma. The development began in
May 2014.

It is developed on GitHub: https://github.com/MartinThoma/hwrt

You can file issues and feature requests there. Alternatively, you can send
me an email: info@martin-thoma.de

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

Sphinx makes use of `reStructured Text <http://openalea.gforge.inria.fr/doc/openalea/doc/_build/html/source/sphinx/rest_syntax.html>`_

The documentation can be built with ``make html``.



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