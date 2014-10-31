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

Project structure
-----------------

The project structure is


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