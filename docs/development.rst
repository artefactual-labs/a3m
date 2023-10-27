===========
Development
===========

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
