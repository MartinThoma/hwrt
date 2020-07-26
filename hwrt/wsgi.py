"""
Use this for web servers.

    gunicorn hwrt.wsgi:app
"""

# First party modules
from hwrt.serve import app  # noqa
