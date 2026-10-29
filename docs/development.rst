===========
Development
===========

Acceptance tests
----------------

The ``Run E2E tests`` CI job builds the production Dockerfile with Docker
Buildx, then imports the image into a Python `Dagger`_ module. Three
``pytest-bdd`` scenarios exercise the installed ``a3m`` command: a directory
containing a JPEG 2000 image with spaces in its filename, a missing source,
and an ingest with S3 storage enabled. Successful ingest must produce a
valid BagIt AIP with the unchanged original, a TIFF preservation copy, and
PREMIS fixity and normalization relationships in METS.

The S3 scenario uses an ephemeral `Argmin`_ service with test credentials and
a fresh bucket. It checks that the uploaded object is keyed by the package
UUID, downloads it, compares its bytes with the local AIP, and repeats the
preservation checks on the downloaded archive. Dagger builds Argmin from the
pinned revision in ``.dagger/src/ci/main.py`` using its Cargo lockfile and
cache mounts. Service data is discarded after the run. No cloud account is
required.

Install Dagger **0.21.11** and start a Docker-compatible container engine, then
run from the repository root::

    make acceptance

This builds the image, runs the scenarios, and exports JUnit results and CLI
logs to ``acceptance/reports/``, including after test failures. CI uploads
the same files as the ``acceptance-reports`` artifact.

The test tools have their own locked environment in ``acceptance/``. Dagger
installs it inside the application container without changing the application's
Python environment. No host Python environment or running a3m service is needed.
The first build needs network access to fetch images and dependencies; the test
input itself is generated locally with FFmpeg.

To run against an existing image and export reports separately::

    docker save --output /tmp/a3m-acceptance.tar a3m:acceptance
    dagger call acceptance --image=/tmp/a3m-acceptance.tar \
        export --path=acceptance/reports
    test "$(cat acceptance/reports/exit-code.txt)" = "0"

The Dagger function exports reports even when pytest fails. The saved exit code
must be checked to determine success; ``make acceptance`` and CI do this
automatically. Status, JUnit results, and logs always come from the same run.
Reports and local virtual environments are excluded from the test inputs.
Docker handles the build because Dagger 0.21.11's Dockerfile converter does not
support all instructions in the production Dockerfile. CI retains its Buildx
layer cache and does not require Dagger Cloud credentials.

The production Dockerfile targets AMD64 package repositories. An ARM development
environment needs an equivalent local Dockerfile supplied explicitly::

    make acceptance ACCEPTANCE_DOCKERFILE=/path/to/Dockerfile.arm64

CI always builds the repository's production Dockerfile on AMD64.

.. _Dagger: https://docs.dagger.io/
.. _Argmin: https://github.com/justincormack/argmin

Python SDK
----------

You may have already learned that a3m comes with two executables: **a3m** and
**a3md**. These are command-line interfaces wrapping a number of Python
abstractions that we are also making available to software developers planning
to build new applications embedding or communicating with a3m.

:func:`a3m.server.runner.create_server` is a function that helps you create
your own instance of :class:`a3m.server.runner.Server`, the gRPC server.

Use :class:`a3m.server.rpc.client.Client` to communicate with it.
:class:`a3m.cli.client.wrapper.ClientWrapper` is a context manager that makes
easier to access to both an embedded server and its client instance.

For more details, see: https://gist.github.com/sevein/2e5cf115c153df1cfc24f0f9d67f6d2a.

.. warning::

   These APIs are still unstable, expect changes!

The following is an example of a web application that uses the development kit
to embed a3m and make it available to web clients.

.. literalinclude:: ../examples/webapp.py


gRPC API
--------

Whether you are embedding a3m or communicating with remote instances, its gRPC
API is the underlying communication system and you should be able to put it in
practice given any of the languages supported by the `gRPC
stack <https://grpc.io/docs/>`_.

gRPC uses Protocol Buffers as the Interface Definition Language (IDL) for
describing both the service interface and the structure of the payload messages.

So far the whole definition of messages and services fits in a single file that
we share below. Writing your custom client isn't hard because the stubs are
automatically generated. Alternatively, it is possible to use a client such as
`grpccurl <https://github.com/fullstorydev/grpcurl>`_ which dynamically browses
our service schema.

.. _idl:

Find the generated documentation of the a3m API at `buf.build/artefactual/a3m`_.

Reference
---------

.. autofunction:: a3m.server.runner.create_server

.. autoclass:: a3m.server.runner.Server
    :undoc-members:

.. autoclass:: a3m.server.rpc.client.Client
    :undoc-members:

.. autoclass:: a3m.cli.client.wrapper.ClientWrapper


.. _`buf.build/artefactual/a3m`: https://buf.build/artefactual/a3m
