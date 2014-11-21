View Data
================================

This tool lets you view a single recording. You can apply preprocessing
steps by specifying a model folder.

.. code:: bash

    $ hwrt view --help
    usage: hwrt view [-h] [-i ID] [--mysql MYSQL] [-m FOLDER] [-l] [-s] [-r]

    optional arguments:
      -h, --help            show this help message and exit
      -i ID, --id ID        which RAW_DATA_ID do you want?
      --mysql MYSQL         which mysql configuration should be used?
      -m FOLDER, --model FOLDER
                            where is the model folder (with a info.yml)?
      -l, --list            list all raw data IDs / symbol IDs
      -s, --server          contact the MySQL server
      -r, --raw             show the raw recording (without preprocessing)

The following image shows how ``hwrt view`` displays an image. The different
colors correspond to different strokes.

.. image:: interrupted-stroke.png
    :width: 512px
    :align: center
    :alt: Recording as showed by ``hwrt view``