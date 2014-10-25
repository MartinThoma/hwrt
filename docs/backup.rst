Backup from MySQL server
================================

This tool is only useful if you also have a `write-math <https://github.com/MartinThoma/write-math>`_
MySQL server running.

.. code:: bash

 $ backup.py --help
 usage: backup.py [-h] [-d FOLDER] [-s] [-o]
 
 Download raw data from online server and back it up (e.g. on DropBox)
 handwriting_datasets.pickle.
 
 optional arguments:
   -h, --help            show this help message and exit
   -d FOLDER, --destination FOLDER
                         where do write the handwriting_dataset.pickle
                         (default: /home/moose/Downloads/write-math/archive
                         /raw-datasets)
   -s, --small           should only a small dataset (with all capital letters)
                         be created? (default: False)
   -o, --onlydropbox     don't download new files; only upload to DropBox
                        (default: False)

