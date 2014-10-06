try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Handwriting Recognition Tools',
    'author': 'Martin Thoma',
    'url': 'https://github.com/MartinThoma/hwrt',
    'download_url': 'https://github.com/MartinThoma/hwrt',
    'author_email': 'info@martin-thoma.de',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['hwrt'],
    'scripts': [],
    'name': 'hwrt'
}

setup(**config)
