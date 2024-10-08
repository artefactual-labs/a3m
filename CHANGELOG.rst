=========
Changelog
=========

..
   All enhancements and patches to scriv will be documented
   in this file.  It adheres to the structure of http://keepachangelog.com/ ,
   but in reStructuredText instead of Markdown (for ease of incorporation into
   Sphinx documentation and the PyPI description).

   This project adheres to Semantic Versioning (http://semver.org/).

Unreleased
==========

See the fragment files in the `changelog.d directory`_.

.. _changelog.d directory: https://github.com/artefactual-labs/a3m/tree/master/changelog.d

.. scriv-insert-here

.. _changelog-0.8.1:

0.8.1 - 2024-09-25
==================

Changed
-------

- Fix docker build.

.. _changelog-0.8.0:

0.8.0 - 2024-09-25
==================

Changed
-------

- Use Python 3.12.6.
- Use ``uv`` to manage the project environment.

.. _changelog-0.7.14:

0.7.14 - 2024-09-24
===================

Changed
-------

- Update dependencies.
- Describe application version in ``pyproject.toml``.

.. _changelog-0.7.13:

0.7.13 - 2024-08-15
===================

Changed
-------

- Use Python 3.12.5.
- Update dependencies.

.. _changelog-0.7.12:

0.7.12 — 2024-07-16
===================

Changed
-------

- Use Python 3.12.4.
- Update dependencies.

.. _changelog-0.7.11:

0.7.11 — 2024-04-19
===================

Changed
-------

- Use Python 3.12.3.
- Replace ``pip``, ``pip-tools`` and ``virtualenv`` with ``uv``.
- Update dependencies.

.. _changelog-0.7.10:

0.7.10 — 2024-03-21
===================

Changed
-------

- Update dependencies.

.. _changelog-0.7.9:

0.7.9 — 2024-02-12
==================

Fixed
-----

- Adjusted server tolenace to more frequent keepalive pings, mitigating
  ``ENHANCE_YOUR_CALM`` errors by allowing shorter intervals between pings.

.. _changelog-0.7.8:

0.7.8 - 2024-02-12
==================

Changed
-------

- Replace bandit with Ruff's flake8-bandit rules.

.. _changelog-0.7.7:

0.7.7 — 2024-02-09
==================

Added
-----

- Automate the build and plublishing of the container image to GitHub Container
  Registry.

Fixed
-----

- Pass arguments to atool using a list, allowing transfer names to contain
  spaces. See issue #449 for more details.

Changed
-------

- Use Python 3.12.2.
- Update dependencies.

.. _changelog-0.7.6:

0.7.6 — 2024-01-22
==================

Added
-----

- Publish to PyPI with Trusted Publishing.

Changed
-------

- Update dependencies.

.. _changelog-0.7.5:

0.7.5 — 2023-12-13
==================

Changed
-------

- Use Python 3.12.1.
- Update dependencies.

Fixed
-----

- Fake ``pkg_resources`` to enable the use of bagit-python in Python 3.12.

0.7.4 — 2023-12-12
==================

Changed
-------

- Use ``platformdirs`` instead of ``appdirs`` to determine the user data
  directory.
- Update dependencies.

Fixed
-----

- Update the Submit RPC handler to use the default processing configuration when
  the user-provided ``config`` field is unset.

.. _changelog-0.7.3:

0.7.3 — 2023-11-30
==================

Changed
-------

- Update dependencies.

.. _changelog-0.7.2:

0.7.2 — 2023-11-08
==================

Changed
-------

- Update dependencies.

.. _changelog-0.7.1:

0.7.1 — 2023-10-30
==================

Fixed
-----

- Fix issue in the setuptools package discovery configuration introduced in the
  migration to ``pyproject.toml``.

.. _changelog-0.7.0:

0.7.0 — 2023-10-28
==================

Removed
-------

- Remove unused dependency: vcrpy.
- Remove ``externals`` (fiwalk extension for ISO disk images).
- Remove virus scanning capabilities.
- Remove UUID log files that were included in AIPs.
- Remove ``null`` values from the JSON-encoded workflow, reducing the size of
  the default workflow document significantly.

Added
-----

- Add scriv to manage our changelog.
- Add pyright, another static type checker that integrates well with Visual
  Studio Code. We should remove mypy at some point.
- Add django-types, type stubs for Django compatible with pyright.
- Add ``make workflow`` to render the current workflow in the browser using
  the latest version of amflow available.
- Add ``tox -e publish`` to build and publish the packages to PyPI.

Changed
-------

- Add time precision to values written to ``premis:dateCreatedByApplication``.
- Bump supported versions of Python to 3.11 and 3.12.
- Ruff is now used for linting and formatting, replacing flake8, black or
  pyupgrade. More tools may be removed as the Ruff team adds more features,
  e.g. bandit, vulture...
- The project has been migrated to ``pyproject.toml`` entirely, ``setup.cfg``
  and ``setup.py`` were removed, as well as other configuration files like
  ``tox.ini``, ``pytest.ini`` or ``.bandit``.
- Multiple improvements in CI, e.g.: image caching for faster builds, use of
  ``.python-version``, combined coverage data across multiple Python versions,
  use of tox without Docker for unit testing.
- ``fpr`` is not a Django app anymore but a standard Python package with new
  abstractions to load rules directly from JSON-encoded documents generated by
  Archivematica. Fetching new rules from Archivematica is now easier, see
  :doc:`contributing` for more. This change allows for future developments
  where multiple ``fpr`` could be supported.

Fixed
-----

- The Docker image is now built using ``requirements.txt`` instead of
  ``requirements-dev.txt`` and uses ``.python-version`` to find the default
  Python version preferred by the project.
- Twine now uses ``.pypirc`` for credentials.
- The docs site now shows the last known release version using
  ``git describe --tags --abbrev=0`` as opposed to relying on
  ``a3m.__version__``. This ensures that the docs site shows the latest
  published release as opposed to the latest release in development.

.. _changelog-0.6.0:

0.6.0 — 2023-09-19
==================

Removed
-------

- Remove ``fileFormatIdentification`` logfile.
- Remove unused dependency ``ufraw``.
- Remove transfer METS file (client script ``create_transfer_mets``).

Added
-----

- Add ```.python-version``, a file indicating the default version of Python to
  be used in this project in various contexts, e.g. Docker image, tooling,
  etc...
- Add processing configuration choice for file format identification of metadata
  files.
- Add ``Empty`` method to the gRPC API (``TransferService``) to manually clean
  up local shared folders. This is a temporary solution until a3m learns to do
  it automatically.
- Add GitHub issue templates.
- Add settings ``org_id`` and ``org_name`` enabling the customization of the
  organization agent.

Changed
-------

- Bump supported versions of Python to 3.11 and 3.12.
- Update other dependencies, including Django 3.2.
- Don't use ``examine_contents`` in the default processing configuration.
- Change the workflow to execute file format identification of metadata files
  if ``identify_submission_and_metadata`` is enabled.
- Refactor multiple client scripts with the goal of improved performance and use
  of short-lived database transactions.
- In the Docker image: use pyenv to manage the installation of Python, use
  Ubuntu 22.04 as the base distribution and the Archivematica 1.15 PPAs for the
  installation of dependencies.
- Use local XML schemas for XML validation, enabling the use of a3m without
  Internet access.
- Change filename cleanup job to filename change.

Fixed
-----

- Fix a bug in ``normalize.py`` breaking normalization.
- Fix ``CheckCloseConnectionsHandler``, a thin wrapper used for database usage
  debugging purposes.
- Fix a bug in ``PoolTaskBackend`` attempting to write to the database after the
  batched jobs had already been delivered to the thread pool, causing sporadic
  errors in the presence of multiple database writers. The task backend now
  writes the tasks before the jobs are delivered to the pool.
- Migrate from Buf remote generation alpha to v1.

.. _changelog-0.5.0:

0.5.0 — 2020-10-27
==================

Added
-----

- Add request-scoped processing configuration.

.. _changelog-0.4.0:

0.4.0 — 2020-10-20
==================

Removed
-------

- Remove reingest capabilities.
- Remove UnitVariable links.
- Remove access normalization paths.
- Remove PID binding.
- Remove access directory support.
- Remove policy check on access derivatives.
- Remove reingest capabilities.

.. _changelog-0.3.1:

0.3.1 — 2020-08-26
==================

Changed
-------

- Change Docker image registry: ``ghcr.io/artefactual-labs/a3m``.

Fixed
-----

- Fix ``long_description`` config in ``setup.cfg``.

.. _changelog-0.3.0:

0.3.0 — 2020-08-26
==================

Added
-----

- Add Sphinx documentation project.

.. _changelog-0.2.1:

0.2.1 — 2020-08-24
==================

Changed
-------

- Disable ``zip_safe`` flag in ``setuptools`` to work around a release problem.

.. _changelog-0.2.0:

0.2.0 — 2020-08-24
==================

Added
-----

- Add a3m (``a3m.cli.client.__main__``) entry point: the a3m client with the
  ability to connect to a remote sever or standalone (embedded engine).
- Add a3md (``a3m.cli.server.__main__``) entry point: the a3m standalone server.

Changed
-------

- Enable WAL mode in SQLite providing more concurrency as readers don't block
  writers and writers don't block readers.
- Remove Gearman-related capabilities in favor of a new threaded pool task
  backend to execute jobs.

.. _changelog-0.1.0:

0.1.0 — 2020-05-31
==================

Amidst the global pandemic, our team found purpose in creating a3m, an internal
project that kept us connected and productive during a time of isolation. This
initiative, an offshoot from Archivematica, focuses on Automated Information
Processing (AIP) creation. a3m removes complexities like the dashboard and the
storage service, pivoting towards a tool that's simpler and more integrative.

See the `full list of commits`_ for more details.


.. _full list of commits: https://github.com/artefactual-labs/a3m/compare/3e524947...v0.1.0
