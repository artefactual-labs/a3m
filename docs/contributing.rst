============
Contributing
============

Dependency management
---------------------

Python dependencies
^^^^^^^^^^^^^^^^^^^

The requirements are listed in ``/pyproject.toml``. The constraints are relaxed
with the purpose of allowing a3m to be used as a library.

We use `pip-tools` which pins the requirements in ``requirements.txt`` and
``requirements-dev.txt`` for our Docker image. Some examples:

* Update dependencies with::

   make pip-compile

* Update all dependencies with::

   make pip-upgrade

Python version
^^^^^^^^^^^^^^

There is a pinned version of Python in ``/.python-version`` that we use when
packaging our Docker image and other development-oriented tools. The preference
is to use the latest version available. Currently:

.. include:: ../.python-version
   :code:

But we aim to support at least a couple of versions, e.g. 3.11 and 3.12 to
provide greater flexibility since a3m is also distributed as a Python package
serving both as an application and a library. We're using tox to test against
multiple versions of Python. If you want to alter the list of versions we're
testing and supporting, the following files must be considered:

* ``pyproject.toml`` describes the minimum version supported
  (``requires-python``), a list of all versions supported (``classifiers``) and
  test environments (under ``[tool.tox]``)
* ``.github/workflows/test.yml`` lists the testing matrix in CI.

Releases
--------

1. Update ``a3m.__version__``, commit and push (see `example <https://github.com/artefactual-labs/a3m/commit/2cbeb6c6fa7e6378ae98fc65a14c97c7f968f7d7>`_).
2. Create git tag, e.g. ``v0.6.0``.
3. Run ``make publish`` to publish the package to PyPI.
