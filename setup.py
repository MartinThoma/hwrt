# Third party modules
from setuptools import setup

requires_tests = ["pytest", "pytest-cov", "pytest-flake8"]
requires_visualization = ["matplotlib"]

requires_all = requires_tests + requires_visualization

setup(
    package_data={"hwrt": ["templates/*", "misc/*"]},
    install_requires=[
        "click",
        "dropbox",
        "Flask",
        "flask-bootstrap",
        "gevent",
        "gunicorn",
        "h5py",
        "keras",
        "natsort",
        "nntoolkit",
        "Pillow",  # Image
        "pymysql",
        "PyYAML",
        "requests",
        "six",
    ],
    extras_require={
        "all": requires_all,
        "visualization": requires_visualization,
        "tests": requires_tests,
    },
)
