#!/usr/bin/env python
# encoding: utf-8

"""
TL;DR pipless let's you install packages as they are needed without
requiring code modification.

pipless hooks the import process and automatically installs packages
if they are not present in the current environment. By default
pipless will create a virtual environment into which packages
are installed.

The pipless module is intended to be run with the "-m" argument to
the python executable:

    python -m pipless [script_path [args..]]

If no script path is given, pipless will drop the user into an
interactive shell after activating a virtual environment and setting
up the pipless import hooks.

If a script path is given, the pipless import hooks will be installed
prior to running the script.

pipless can also be explicitly imported into the source code. Doing
so will install the necessary hooks and activate the virtual
environment.

The pipless experience becomes especially seamless when an alias
is made for python in your ~/.bashrc. E.g. alias python="python
-m pipless"

See https://github.com/d0c-s4vage/pipless for more details.
"""


import os, sys
from setuptools import setup


setup(
    # metadata
    name             = 'pipless',
    description      = 'Too much pip? Install packages on import without changing your code.',
    long_description = __doc__,
    license          = 'MIT',
    version          = '1.0',
    author           = 'James "d0c_s4vage" Johnson',
    maintainer       = 'James "d0c_s4vage" Johnson',
    author_email     = 'd0c.s4vage@gmail.com',
    url              = 'https://github.com/d0c-s4vage/pipless',
    platforms        = 'Cross Platform',
	download_url     = "https://github.com/d0c-s4vage/pipless/tarball/v1.0",
	install_requires = ["virtualenv"],
    py_modules       = ['pipless'],
    classifiers      = [
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    scripts          = [
        os.path.join("scripts", "pipless")
    ]
)
