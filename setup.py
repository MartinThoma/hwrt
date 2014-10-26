try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'name': 'hwrt',
    'version': '0.1.115',
    'author': 'Martin Thoma',
    'author_email': 'info@martin-thoma.de',
    'packages': ['hwrt'],
    'scripts': ['bin/backup.py', 'bin/view.py', 'bin/download.py',
                'bin/test.py', 'bin/train.py', 'bin/analyze_data.py',
                'bin/hwrt', 'bin/record.py'],
    'package_data': {'hwrt': ['templates/*', 'misc/*']},
    'url': 'https://github.com/MartinThoma/hwrt',
    'license': 'MIT',
    'description': 'Handwriting Recognition Tools',
    'long_description': """A tookit for handwriting recognition. It was
    developed as part of the bachelors thesis of Martin Thoma.""",
    'install_requires': [
        "argparse",
        "theano",
        "nose",
        "natsort"
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
                    'Topic :: Scientific/Engineering :: Artificial Intelligence',
                    'Topic :: Software Development',
                    'Topic :: Utilities'],
    'zip_safe': False,
    'test_suite': 'nose.collector'
}

setup(**config)
