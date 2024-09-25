============
Contributing
============

Dependency management
---------------------

Python dependencies
^^^^^^^^^^^^^^^^^^^

The requirements are listed in ``/pyproject.toml``. We use ``uv`` to manage the
project environment, including the ``uv.lock`` lockfile.

Create and activate the virtual environment with::

    $ uv sync --dev
    $ source .venb/bin/activate

Update the lockfile allowing package upgrades::

    $ uv lock --upgrade

At this point you can also look up new versions beyond our constraints, e.g.::

    $ uv run --with=pip pip list --outdated

The `project lockfile`_ documentation page describes other operations such as
upgrading locked package versions individually.

pre-commit
^^^^^^^^^^

pre-commit is a framework we use for managing and maintaining pre-commit hooks.
The easiest way to discover and apply new updates is to run::

    $ pre-commit autoupdate

Commit the changes and run pre-commit again with::

    $ pre-commit run --all-files

Python version
^^^^^^^^^^^^^^

There is a pinned version of Python in ``/.python-version`` that we use when
packaging our Docker image and other development-oriented tools. The preference
is to use the latest version available. Currently:

.. include:: ../.python-version
   :code:

Releases
--------

We aim to further enhance and automate our release process.

Please adhere to the following instructions:

1. Update the changelog (use ``scriv collect`` to populate ``CHANGELOG.rst``).
   Submit these changes through a pull request and merge it once all checks have
   passed.
2. Confirm that the checks are also passing in ``main``.
3. Create and push the git tag, e.g.::

    $ git tag v0.7.7
    $ git push origin refs/tags/v0.7.7

   This should have triggered the publishing workflow. Please confirm that the
   new version of the package is available on `PyPI`_ and that the container
   image has been published to the `GitHub Container Registry`_.

Import FPR dataset from Archivematica
-------------------------------------

a3m loads the FPR dataset from a JSON document
(``a3m/fpr/migrations/initial-data.json``) generated from the upstream
Archivematica project. This section describes how to generate it:

In Archivematica, generate a dump with::

    manage.py dumpdata --format=json fpr

Remove unused models from the document::

    jq --sort-keys --indent 4 '[.[] | select(.model == "fpr.format" or .model == "fpr.formatgroup" or .model == "fpr.formatversion" or .model == "fpr.fpcommand" or .model == "fpr.fprule" or .model == "fpr.fptool")]' fpr-dumpdata.json > output.json

Replace the dataset::

    mv output.json ../../a3m/fpr/migrations/initial-data.json

From the root directory, run the registry sanity checks::

    pytest tests/test_registry.py

Based on the validation issues reported, fix as needed. Make sure that the
``fiwalk`` command is not using a ficonfig file.


.. _PyPI: https://pypi.org/project/a3m/
.. _GitHub Container Registry: https://ghcr.io/artefactual-labs/a3m
.. _project lockfile: https://docs.astral.sh/uv/concepts/projects/#project-lockfile
