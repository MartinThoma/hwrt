from setuptools import find_packages
from setuptools import setup

config = {
    'name': 'hwrt',
    'version': '0.1.221',
    'author': 'Martin Thoma',
    'author_email': 'info@martin-thoma.de',
    'maintainer': 'Martin Thoma',
    'maintainer_email': 'info@martin-thoma.de',
    'packages': find_packages(),
    'scripts': ['bin/hwrt', 'bin/test.py', 'bin/train.py'],
    'package_data': {'hwrt': ['templates/*', 'misc/*']},
    'platforms': ['Linux', 'MacOS X', 'Windows'],
    'url': 'https://github.com/MartinThoma/hwrt',
    'license': 'MIT',
    'description': 'Handwriting Recognition Tools',
    'long_description': ("A tookit for handwriting recognition. It was "
                         "developed as part of the bachelors thesis of "
                         "Martin Thoma."),
    'install_requires': [
        "argparse",
        "theano",
        "nose",
        "natsort",
        "PyYAML",
        "matplotlib",
        "nntoolkit",
        "h5py",
        "flask",
        "flask-bootstrap",
        "requests",
        "six"
    ],
    'keywords': ['HWRT', 'recognition', 'handwriting', 'on-line'],
    'download_url': 'https://github.com/MartinThoma/hwrt',
    'classifiers': ['Development Status :: 3 - Alpha',
                    'Environment :: Console',
                    'Intended Audience :: Developers',
                    'Intended Audience :: Science/Research',
                    'License :: OSI Approved :: MIT License',
                    'Natural Language :: English',
                    'Programming Language :: Python :: 2.7',
                    'Programming Language :: Python :: 3',
                    'Programming Language :: Python :: 3.3',
                    'Programming Language :: Python :: 3.4',
                    'Topic :: Scientific/Engineering :: Artificial Intelligence',
                    'Topic :: Software Development',
                    'Topic :: Utilities'],
    'zip_safe': False,
    'test_suite': 'nose.collector'
}

setup(**config)
