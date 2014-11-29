Plugins
=======

You eventually want to create your own preprocessing steps, your own
features or another implementation of the same feature. You can do so by
specifying a Python script in ``preprocessing`` or ``features``.

If a preprocessing class or a feature class exists in the official hwrt and
in a plugin simultaniously, the hwrt implementation is used.

Preprocessing Classes
---------------------

Every feature class must have a ``__str__``, ``__repr__`` and a ``__call__``
function where

* ``__call__`` must take exactly one argument of type HandwrittenData
* ``__call__`` must call the :mod:`Handwriting.set_points`


Feature Classes
---------------

Every feature class must have a ``__str__``, ``__repr__``, ``__call__`` and
``get_dimension`` function where

* ``__call__`` must take exactly one argument of type HandwrittenData
* ``__call__`` must return a list of length ``get_dimension()``
* ``get_dimension`` must return a positive number
* have a 'normalize' attribute that is either true or false


Preprocessing Plugin Example
----------------------------

.. code-block:: python

    #!/usr/bin/env python
    # -*- coding: utf-8 -*-

    import hwrt.HandwrittenData as HandwrittenData


    class Nullify(object):
        def __repr__(self):
            return "Nullify"

        def __str__(self):
            return "Nullify"

        def __call__(self, handwritten_data):
            assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
                "handwritten data is not of type HandwrittenData, but of %r" % \
                type(handwritten_data)
            # pointlist = handwritten_data.get_pointlist()
            new_pointlist = []
            new_stroke = []
            new_stroke.append({'x': 0, 'y': 0, 'time': 0})
            new_pointlist.append(new_stroke)
            handwritten_data.set_pointlist(new_pointlist)

Feature Plugin Example
----------------------

.. code-block:: python

    #!/usr/bin/env python
    # -*- coding: utf-8 -*-

    import hwrt.HandwrittenData as HandwrittenData


    class StrokeCountTata(object):

        """Stroke count as a 1 dimensional recording."""

        normalize = True

        def __repr__(self):
            return "StrokeCount"

        def __str__(self):
            return "stroke count"

        def get_dimension(self):
            return 1

        def __call__(self, handwritten_data):
            assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
                "handwritten data is not of type HandwrittenData, but of %r" % \
                type(handwritten_data)
            return [len(handwritten_data.get_pointlist())]
