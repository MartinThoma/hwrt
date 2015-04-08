Analyze Data
============

This tool helps to analyze data by features.


General usage
-------------

.. code:: bash

    $ hwrt analyze_data --help
    usage: hwrt analyze_data [-h] [-d FILE] [-f]

    optional arguments:
      -h, --help            show this help message and exit
      -d FILE, --handwriting_datasets FILE
                            where are the pickled handwriting_datasets?
      -f, --features        analyze features



Plug-in System
---------------

It can be extended by a plugin system. To do so, the configuration file
``~/.hwrtrc`` has to be edited. The following two entries are important:

.. code:: bash

    data_analyzation_plugins: /home/moose/Desktop/da.py 
    data_analyzation_queue: 
      - TrainingCount:
        - filename: trainingcount.csv
      - Creator: null

The value of ``data_analyzation_plugins`` indicates where the file with
self-written data analyzation classes is located. Could could looke like this:


.. code:: python

    #!/usr/bin/env python
    # -*- coding: utf-8 -*-

    import time
    from collections import defaultdict

    # hwrt modules
    from hwrt import HandwrittenData
    from hwrt import utils
    from hwrt import data_analyzation_metrics
    from hwrt import geometry


    class TrainingCount(object):
        """Analyze how many training examples exist for each recording."""

        def __init__(self, filename="creator.csv"):
            self.filename = data_analyzation_metrics.prepare_file(filename)

        def __repr__(self):
            return "TrainingCount(%s)" % self.filename

        def __str__(self):
            return "TrainingCount(%s)" % self.filename

        def __call__(self, raw_datasets):
            write_file = open(self.filename, "a")
            write_file.write("symbol,trainingcount\n")  # heading

            print_data = defaultdict(int)
            start_time = time.time()
            for i, raw_dataset in enumerate(raw_datasets):
                if i % 100 == 0 and i > 0:
                    utils.print_status(len(raw_datasets), i, start_time)
                print_data[raw_dataset['handwriting'].formula_in_latex] += 1
            print("\r100%"+"\033[K\n")
            # Sort the data by highest value, descending
            print_data = sorted(print_data.items(),
                                key=lambda n: n[1],
                                reverse=True)
            # Write data to file
            write_file.write("total,%i\n" %
                             sum([value for _, value in print_data]))
            for userid, value in print_data:
                write_file.write("%s,%i\n" % (userid, value))
            write_file.close()


Default metrics
---------------
There are also many ready-to-use metrics:

.. automodule:: hwrt.data_analyzation_metrics
   :members: