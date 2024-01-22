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
``requirements-dev.txt`` for our Docker image. We provide a couple of helpers:

* ``make pip-compile`` generates the requirements with the latest versions of
  dependencies that satisfy the constraints in ``pyproject.toml``, but does not
  update versions if they are already satisfied.
* ``make pip-upgrade`` regenerates the requirements, forcibly upgrading all
  listed packages to their latest available versions within the constraints.

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

1. Make sure that ``a3m.__version__`` reflects the new version.
2. Make sure that the changelog has been updated.
   Use ``scriv collect`` to populate ``CHANGELOG.rst``, submit the changes.
3. Create and push git tag, e.g.::

    $ git tag v0.7.1
    $ git push origin refs/tags/v0.7.1

   This should have triggered the publishing workflow. Confirm that the new
   version of the package is in `PyPI <https://pypi.org/project/a3m/>`_.

4. Build Docker image::

    $ docker build \
      -t ghcr.io/artefactual-labs/a3m:latest \
      -t ghcr.io/artefactual-labs/a3m:v0.7.1 \
        .
5. Push Docker image to the registry::

    $ docker push ghcr.io/artefactual-labs/a3m:latest
    $ docker push ghcr.io/artefactual-labs/a3m:v0.7.2
