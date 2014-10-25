Installation
============

The ``hwrt`` toolkit can be installed via pip:

.. code:: bash

    # pip install hwrt

However, you might have to install some packages first for ``scipy``. On
Debian-based systems you can do this with the following commands:

.. code:: bash

    # apt-get install libblas-dev liblapack-dev gfortran
    # apt-get install python-scipy python-numpy

Now you can install the remaining packages:

.. code:: bash

    # pip install natsort matplotlib coveralls shapely
    # pip install numpy
    # pip install scipy

Now you can install `pfile_utils`_. Some explanation of what they
are can be found at `my blog`_

As a last step, you can install hwrt:

.. code:: bash

    # pip install hwrt

You can check if it worked by

.. code:: bash

    $ hwrt --version
    hwrt 0.1.101

Please send me an email (info@martin-thoma.de) if that didn't work.


nntoolkit
---------

In order to use `hwrt` completely (especially testing, training and record.py)
you have to have an executable ``nntoolkit`` that supports the following usages:

.. code:: bash

    $ nntoolkit run --batch-size 1 -f%0.4f <test_file> < <model>

has to output the evaluation result in standard output as a list of floats
separated by newlines ``\n+``. The evaluation result might either be the
index of the neuron with highest activation or the list of probabilities
of each class separated by spaces.

.. code:: bash

    $ nntoolkit make mlp <topology>

has to print the model in standard output.

The `hwrt` toolset is independent of the way the training command is
formatted as the training command gets inserted directly into the configuration
file ``info.yml`` of the model.

In order to implement such a neural network executable one can use Theano,
cuDNN_ or Caffe_. Deeplearning_ contains example code for multilayer perceptrons
written with Theano (Python).


Upgrading hwrt
--------------

Upgrading hwrt to the latest version is much easier:

.. code:: bash

    # pip install hwrt --upgrade

.. _`pfile_utils`: http://www1.icsi.berkeley.edu/~dpwe/projects/sprach/sprachcore.html
.. _my blog: http://martin-thoma.com/what-are-pfiles/
.. _Python: http://www.python.org/
.. _Caffe: http://caffe.berkeleyvision.org/
.. _cuDNN: https://developer.nvidia.com/cuDNN
.. _Deeplearning: http://www.deeplearning.net/tutorial/