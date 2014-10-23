Model Testing
=============

This tool calculates the error of a model according to different error
measures.

The options `-n` and `--merge` should not be used together.

.. code:: bash

 $ test.py --help
 usage: test.py [-h] [-m FOLDER] [-s {test,train,valid}] [-n N] [--merge]
 
 Get the error of a model. This tool supports multiple error measures.
 
 optional arguments:
   -h, --help            show this help message and exit
   -m FOLDER, --model FOLDER
                         where is the model folder (with the info.yml)?
                         (default: current folder)
   -s {test,train,valid}, --set {test,train,valid}
                         which set should get analyzed? (default: test)
   -n N                  Top-N error (default: 3)
   --merge               merge problem classes that are easy to confuse
                         (default: False)

