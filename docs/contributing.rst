============
Contributing
============

Dependency management
---------------------

Python dependencies
^^^^^^^^^^^^^^^^^^^

The requirements are listed in ``/setup.cfg`` under (``install_requires``). The
constraints are relaxed with the purpose of allowing a3m to be used as a
library.

We use `pip-tools` which pins the requirements in ``requirements.txt`` and
``requirements-dev.txt`` for our Docker image. Some examples:

* Update dependencies with::
 
   pip-compile --output-file=requirements.txt setup.py

* Update all dependencies with::

   pip-compile --upgrade --output-file=requirements.txt setup.py

* Update all development dependencies with::

   pip-compile --extra=dev --upgrade --output-file=requirements-dev.txt setup.py

Python version
^^^^^^^^^^^^^^

We're currently testing only against one version of Python.

The current version is:

.. include:: ../.python-version
   :code:

You can find it in the following files:

* ``/.python-version``
* ``/Dockerfile`` (build argument ``PYTHON_VERSION``)
* ``/.github/workflows/tests.yml``
* ``/setup.cfg`` (attributes ``classifiers`` and ``python_requires``)
* ``/.pre-commit-config.yaml`` (attribute ``default_language_version.python``)

We should relax the constraint as much as possible and test in CI because one of
the aspirations of a3m is to be used as a library.

Releases
--------

1. Update ``a3m.__version__``, commit and push (see `example <https://github.com/artefactual-labs/a3m/commit/2cbeb6c6fa7e6378ae98fc65a14c97c7f968f7d7>`_).
2. Create git tag, e.g. ``v0.6.0``.
3. Run ``make publish`` to publish the package to PyPI.
