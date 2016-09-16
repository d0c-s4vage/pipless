

Mappings
===========

Due to the differences between distribution names and package names
on PyPI, in certain scenarios pipless will be unable to determine
how to install a distribution from the package name.

**NOTE**: *A package name is what you import with (e.g.* ``import flask`` *), a
distribution name is what you pip install with (e.g.* ``pip install Flask`` *).
Package names do not need to (and don't always) match the
distribution name*

Currently no complete mapping exists between the distribution and package
names that are hosted on PyPI. As such, I have started a new project, `pypi_map <https://github.com/d0c-s4vage/pypi_map>`_,
to map all of the package names. Until that project is complete,
pipless makes use of mapping files that allow the user to
explicitly map distribution names to import names.

Mapping File Format
-------------------

The mapping file format is extremely simple. Each mapping is on
its own line. Comments begin with a pound sign (``#``), and empty
lines are ignored.

A mapping consists of the package name (what you import with) followed
by whitespace, and then the distribution name (the name to install it with).

E.g.:

.. code-block:: text

   # this is a comment
   flask  Flask

   yaml   PyYaml # another comment
   jinja2 Jinja2

Locations
---------

Pipless loads mapping files automatically from the two locations:

1. Installation directory

Pipless includes a default ``mappings.txt`` file with its source code.
This can be found at:

.. code-block:: python
   
   import pipless
   os.path.join(os.path.dirname(pipless.__file__), "mapping.txt")

2. User config directory

Pipless also checks for a ``mappings.txt`` at ``~/.config/pipless/mappings.txt``. This file
(and directory tree) is not automatically created.
