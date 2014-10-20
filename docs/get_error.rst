Get Error
================================

This tool calculates the error of a model according to different error
measures.

The options `-n` and `--merge` should not be used together.

.. code:: bash

 $ get_error.py --help
 usage: get_error.py [-h] [-m FOLDER] [-s {test,train,valid}] [-n N] [--merge]
 
 Get the error of a model. This tool supports multiple error measures.
 
 optional arguments:
   -h, --help            show this help message and exit
   -m FOLDER, --model FOLDER
                         where is the model folder (with the info.yml)?
                         (default: /home/moose/Downloads/write-
                         math/archive/models/small-baseline)
   -s {test,train,valid}, --set {test,train,valid}
                         which set should get analyzed? (default: test)
   -n N                  Top-N error (default: 3)
   --merge               merge problem classes that are easy to confuse
                         (default: False)
