#!/usr/bin/env python

# Core Library modules
import os

os.chdir("docs")

os.system("make html")
os.chdir("..")
os.system("python setup.py upload_docs --upload-dir docs/_build/html")
