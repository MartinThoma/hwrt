#!/usr/bin/env python

"""Convert a model with CudaNdarray objects to a model with numpy objects.

This script helps when you train a model with Lasagne / Theano and the GPU,
but you want to evaluate it with a machine which only has a CPU.
"""

# Core Library modules
import logging
import os
import pickle
import sys
import tarfile

# Third party modules
import h5py
import numpy
from theano.sandbox import cuda

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.DEBUG,
    stream=sys.stdout,
)


def main():
    """
    Orchestrate the conversion from a pickled file with CUDA matrices to a tar
    file with hdf5 files.
    """
    matrices = get_matrices()
    create_model_tar(matrices)


def get_matrices():
    """
    Get the matrices from a pickled files.

    Returns
    -------
    list
        List of all matrices.
    """
    with open("hwrt/misc/is_one_symbol_classifier.pickle", "rb") as f:
        a = pickle.load(f)

    arrays = []
    for el1 in a.input_storage:
        for el2 in el1.__dict__["storage"]:
            if isinstance(el2, cuda.CudaNdarray):
                arrays.append({"storage": numpy.asarray(el2), "name": el1.name})
            else:
                logging.warning("was type %s. Do nothing." % type(el2))
                logging.debug(el1.name)
    return arrays


def create_model_tar(matrices, tarname="model-cuda-converted.tar"):
    """
    Create a tar file which contains the model.

    Parameters
    ----------
    matrices : list
    tarname : str
        Target file which will be created.
    """
    # Write layers
    filenames = []
    for layer in range(len(matrices)):
        if matrices[layer]["name"] == "W":
            weights = matrices[layer]["storage"]
            weights_file = h5py.File("W%i.hdf5" % (layer / 2), "w")
            weights_file.create_dataset(weights_file.id.name, data=weights)
            weights_file.close()
            filenames.append("W%i.hdf5" % (layer / 2))
        elif matrices[layer]["name"] == "b":
            b = matrices[layer]["storage"]
            bfile = h5py.File("b%i.hdf5" % (layer / 2), "w")
            bfile.create_dataset(bfile.id.name, data=b)
            bfile.close()
            filenames.append("b%i.hdf5" % (layer / 2))

        # activation = a['layers'][layer]['_props']['activation']
        # activation = activation.replace('sigmoid', 'Sigmoid')
        # activation = activation.replace('softmax', 'Softmax')
        # layers.append({'W': {'size': list(W.shape),
        #                      'filename': 'W%i.hdf5' % layer},
        #                'b': {'size': list(b.shape),
        #                      'filename': 'b%i.hdf5' % layer},
        #                'activation': activation})
    with tarfile.open(tarname, "w:") as tar:
        for name in filenames:
            tar.add(name)

    # Remove temporary files which are now in tar file
    for filename in filenames:
        os.remove(filename)


if __name__ == "__main__":
    main()
