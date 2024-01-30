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
        └── tmp


Processing configuration
------------------------

a3m abandons the XML-based processing configuration document used by
Archivematica. Instead, users are asked to submit the configuration as part
of their transfer requests.

With our client, ``--processing-config`` can be used multiple times to indicate
the desired settings::

    a3m --name="Test" --processing-config="normalize=no" http://...

The Python client can do similarly::

    from a3m.api.transferservice.v1beta1.request_response_pb2 import (
        ProcessingConfig
    )

    c = Client(...)
    c.submit(
        url="URL...", name="Name...",
        config=ProcessingConfig(normalize=False))

The full list of settings or their defaults are not described yet but it can be
found in the `ProcessingConfig`_ message type of the API.

.. _`ProcessingConfig`: https://buf.build/artefactual/a3m/docs/main:a3m.api.transferservice.v1beta1#a3m.api.transferservice.v1beta1.ProcessingConfig
