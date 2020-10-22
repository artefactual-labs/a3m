Usage
=====

Server
------

a3m can be executed in server mode via **a3md**::

    a3md

It launches a gRPC server and several subsystems that enable processing. Use a
service manager such as systemd to configure it as a service.

.. note::

   By default, **a3md** does not log messages with level ``DEBUG`` and
   generally tries to keep the log stream unobstructed unless human
   intervention is required.

   For debugging purposes, you can access to all messages by setting the
   environment string ``A3M_DEBUG==yes``.

Client
------

**a3m** is the command-line interface that aims to provide a rich text-based
user experience. It communicates with the server via gRPC. Use as follows::

    a3m --address=127.0.0.1:7000 ~/Documents/pictures

When the ``--address`` option is not included, **a3m** runs its own embedded
instance of the server::

    a3m ~/Documents/pictures

Processing directory
--------------------

a3m uses a processing directory to store its database and all created AIPs.
If you are using Linux, this directory can be found under `~/.local/share/a3m`
and these are its contents::

    .
    ├── db.sqlite
    └── share
        ├── completed
        │   └── Test-fa1d6cb3-c1fd-4618-ba55-32f01fda8198.7z
        ├── currentlyProcessing
        │   ├── ingest
        │   └── transfer
        ├── failed
        │   ├── 0d117bed-2124-48a2-b9d7-f32514d39c1e
        ├── policies
        ├── processingConfigs
        │   └── default.xml
        └── tmp


.. _devkit:

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

For more details, see: https://gist.github.com/sevein/2e5cf115c153df1cfc24f0f9d67f6d2a.

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
