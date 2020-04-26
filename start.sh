#!/bin/bash
gunicorn --worker-class=gevent --worker-connections=1000 --bind 0.0.0.0:5000 hwrt.wsgi:app --workers=4 --timeout 120 --keep-alive 120
