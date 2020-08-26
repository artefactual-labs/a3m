Usage
=====

Standalone mode
---------------

a3m can run in standalone mode with **a3md**. It starts the gRPC server::

    a3md

**a3m** is the corresponding gRPC client::

    a3m --address=127.0.0.1:7000 ~/Documents/pictures

When the ``--address`` option is not included, **a3m** runs its own instance of
the server::

    a3m ~/Documents/pictures

Development kit
---------------

**a3m** and **a3md** are both command-line interfaces wrapping a number of
abstractions that are also available to Python developers. This is useful if
you are planning to build an application embedding a3m, e.g. a processing
worker that receives tasks off a message queue like Redis.

:func:`a3m.server.runner.create_server` is a function that helps you create your
own instance of :class:`a3m.server.runner.Server`, the gRPC server.

Use :class:`a3m.server.rpc.client.Client` to communicate with it.
:class:`a3m.cli.client.wrapper.ClientWrapper` is a context manager that makes
easier to access to both an embedded server and its client instance.

.. warning::

   These APIs are still unstable, expect changes!

The following is an example of a web application that uses the development kit
to embed a3m and make it available to web clients.

.. literalinclude:: ../examples/webapp.py

Service definition
------------------

gRPC uses Protocol Buffers as the Interface Definition Language (IDL) for
describing both the service interface and the structure of the payload messages.

.. literalinclude:: ../a3m/server/rpc/proto/a3m.proto
   :language: protobuf

Reference
---------

.. autofunction:: a3m.server.runner.create_server

.. autoclass:: a3m.server.runner.Server
    :undoc-members:

.. autoclass:: a3m.server.rpc.client.Client
    :undoc-members:

.. autoclass:: a3m.cli.client.wrapper.ClientWrapper
