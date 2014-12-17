#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Features in development."""

import urllib
import os

# hwrt modules
import hwrt.HandwrittenData as HandwrittenData
import hwrt.utils as utils


class Bitmap(object):

    """n × n grayscale bitmap of the recording."""

    normalize = True

    def __init__(self, n=28):
        self.n = n  # Size of the bitmap (n x n)

    def __repr__(self):
        return ("Bitmap (n=%i)\n") % (self.n)

    def __str__(self):
        return repr(self)

    def get_dimension(self):
        """Get the dimension of the returned feature. This equals the number
           of elements in the returned list of numbers."""
        return self.n**2

    def __call__(self, handwritten_data):
        assert isinstance(handwritten_data, HandwrittenData.HandwrittenData), \
            "handwritten data is not of type HandwrittenData, but of %r" % \
            type(handwritten_data)
        x = []
        url = "http://localhost/write-math/website/raw-data/"
        raw_data_id = handwritten_data.raw_data_id
        project_root = utils.get_project_root()
        foldername = os.path.jon(project_root, "bitmaps")
        f = urllib.urlopen("{url}{id}.svg".format(url=url, id=raw_data_id))
        with open("%s%i.svg" % (foldername, raw_data_id), "wb") as imgFile:
            imgFile.write(f.read())

        command = ("convert -size 28x28 {folder}{id}.svg  -resize {n}x{n} "
                   "-gravity center -extent {n}x{n} "
                   "-monochrome {folder}{id}.png").format(id=raw_data_id,
                                                          n=self.n,
                                                          # url=url,
                                                          folder=foldername)
        os.system(command)
        from PIL import Image
        im = Image.open("%s%i.png" % (foldername, raw_data_id))
        pix = im.load()
        # pixel_image = [[0 for i in range(28)] for j in range(28)]
        for i in range(28):
            for j in range(28):
                # pixel_image[i][j] = pix[i, j]
                x.append(pix[i, j])
        assert self.get_dimension() == len(x), \
            "Dimension of %s should be %i, but was %i" % \
            (str(self), self.get_dimension(), len(x))
        return x
