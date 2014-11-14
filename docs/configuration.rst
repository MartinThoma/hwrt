Configuration
============

The ``hwrt`` toolkit makes use of a configuration file. This file has to be
in the home folder of the user an it has to be called ``.hwrtrc``.

The configuration file is in YAML format. The possible values are:

* ``root``: This is a required configuration entry. Its value must be a path.
  hwrt will look for all configuration files in this path.
* ``nntoolkit``: The name of the executable in your path that does neural
  network training
* ``preprocessing``: A path to a Python script that contains your preprocessing
  classes. Have a look at `the official preprocessing classes <https://github.com/MartinThoma/hwrt/blob/master/hwrt/preprocessing.py>`_
  to see how they should be structured.
* ``features``: Just like preprocessing, this has to be a path to a Python
  script.

There are 3 configurations that are probably only interesting for me:

* ``dbconfig``: Only important if you want to access a MySQL db to get the data
* ``dropbox_app_key`` and ``dropbox_app_secret``: Only important if you want
  to upload data to DropBox


Example
-------

The following is an example ``~/.hwrtrc`` configuration file:

.. code-block:: yaml

    root: /home/moose/GitHub/hwr-experiments
    nntoolkit: nntoolkitfancyname
    preprocessing: /home/moose/hwrt-config/preprocessing.py
    features: /home/moose/hwrt-config/features.py
    dbconfig: /home/moose/hwrt-config/db.config.yml
    dropbox_app_key: 'INSERT_APP_KEY'
    dropbox_app_secret: 'INSERT_APP_SECRET'