Installation
============

The ``hwrt`` toolkit can be installed via pip:

::

    # pip install hwrt

However, you might have to install some packages first for ``scipy``. On
Debian-based systems you can do this with the following commands:

::

    # apt-get install libblas-dev liblapack-dev gfortran
    # apt-get install python-scipy python-numpy

Now you can install the remaining packages:

::

    # pip install natsort matplotlib coveralls shapely
    # pip install numpy
    # pip install scipy

Now you can install ```pfile_utils```_. Some explanation of what they
are can be found at `my blog`_

As a last step, you can install hwrt:

::

    # pip install hwrt

Please send me an email (info@martin-thoma.de) if that didn’t work.

Upgrading hwrt
--------------

Upgrading hwrt to the latest version is much easier:

::

    # pip install hwrt --upgrade

.. _``pfile_utils``: http://www1.icsi.berkeley.edu/~dpwe/projects/sprach/sprachcore.html
.. _my blog: http://martin-thoma.com/what-are-pfiles/