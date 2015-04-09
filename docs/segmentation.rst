segmentation
------------

Segmentation results
--------------------

The first idea how to segment is training a MLP which classifies two strokes
as belonging to one symbol or not. For the best 500 segmentations the symbol
recognizer is run and the score is adjusted.

.. code::

    2015-04-09 05:11:49,077 INFO mean possition of correct segmentation: 37.82
    2015-04-09 05:11:49,077 INFO median possition of correct segmentation: 3.00
    2015-04-09 05:11:49,078 INFO TOP-1: 0.19 correct
    2015-04-09 05:11:49,078 INFO TOP-3: 0.36 correct
    2015-04-09 05:11:49,078 INFO TOP-10: 0.50 correct
    2015-04-09 05:11:49,078 INFO TOP-20: 0.58 correct
    2015-04-09 05:11:49,078 INFO TOP-50: 0.63 correct
    2015-04-09 05:11:49,079 INFO Out of order expressions (e.g. delayed strokes): 72
    2015-04-09 05:11:49,079 INFO Total expressions (non-unique): 943



Module documentation
--------------------


.. automodule:: hwrt.segmentation
   :members:

