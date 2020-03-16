# Third party modules
from setuptools import setup

config = {
    "package_data": {"hwrt": ["templates/*", "misc/*"]},
    "install_requires": [
        "Flask",
        "click",
        "flask-bootstrap",
        "future",
        "h5py",
        "lasagne==0.1",
        "matplotlib",
        "natsort",
        "nntoolkit",
        "pytest",
        "pytest-cov",
        "pytest-flake8",
        "Pillow",  # Image
        "pymysql",
        "PyYAML",
        "requests",
        "six",
        "theano==0.7.0",
    ],
}

setup(**config)
