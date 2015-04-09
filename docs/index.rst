.. hwrt documentation master file, created by
   sphinx-quickstart on Mon Oct 20 16:23:32 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

hwrt documentation
==================

hwrt is short for 'handwriting recognition toolkit'. This toolkit allows you
to download on-line handwritten mathematical symbols, view them, analyze them
and train and test models to classify them automatically. The toolset offers
many preprocessing algorithms and features that can be combined in many ways
by YAML configuration files.

The theoretical part is covered in the bachelor's thesis 'On-line Handwriting
Recognition of Mathematical Symbols' from Martin Thoma. One part of this
bachelor's thesis was to create this toolkit and evaluate it.


All project source code and the source code of this documentation is at
`github.com/MartinThoma/hwrt <https://github.com/MartinThoma/hwrt>`_.
The experiments are at
`github.com/MartinThoma/hwr-experiments <https://github.com/MartinThoma/hwr-experiments>`_.

If you want to talk about this toolkit, you can contact me (Martin Thoma)
via email: info@martin-thoma.de

Contents:

.. toctree::
   :maxdepth: 2

   installation
   configuration
   HandwrittenData
   preprocessing
   data_multiplication
   features
   create_pfiles
   plugins
   development

Commands:

.. toctree::
   :maxdepth: 2

   serve
   download
   analyze_data
   view
   train
   test
   backup

Development

.. toctree::
   :maxdepth: 2

   segmentation
   utils


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

