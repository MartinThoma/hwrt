View Data
================================

This tool lets you view a single recording. You can apply preprocessing
steps by specifying a model folder.

.. code:: bash

    $ view.py --help
    usage: view.py [-h] [-i ID] [--mysql MYSQL] [-m FOLDER] [-l]

    Display a raw_data_id.

    optional arguments:
      -h, --help            show this help message and exit
      -i ID, --id ID        which RAW_DATA_ID do you want? (default: 279062)
      --mysql MYSQL         which mysql configuration should be used? (default:
                            mysql_online)
      -m FOLDER, --model FOLDER
                            where is the model folder (with a info.yml)? (default:
                            /home/moose/GitHub/hwr-experiments/models/small-
                            baseline)
      -l, --list            list all raw data IDs / symbol IDs (default: False)
