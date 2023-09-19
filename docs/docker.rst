======
Docker
======

Our Docker image is extremely convenient because it includes many software
dependencies that you would need to install manually otherwise. Off the shelf,
the Docker image brings an environment with a3m and its dependencies installed
and ready to use.

We're going to describe a couple of different ways in which you can make use of
our Docker image.

Download the latest version
===========================

Make sure that you have the latest version with::

    docker pull ghcr.io/artefactual-labs/a3m:main

CLI with bundled server container
=================================

This section shows the a3m CLI with the processing engine embedded. Using Docker
volumes, we're going to inject a transfer source directory and a destination
for the AIPs that we're creating to ease its extraction.

Prepare the local directories that will host the volumes:

    mkdir -p /tmp/demo/transfers /tmp/demo/completed

Prepare a dummy transfer::

    mkdir -p /tmp/demo/transfers/transfer1 && touch /tmp/demo/transfers/transfer1/hola.txt

Submit ``/tmp/demo/transfers/transfer1`` to an ephemeral a3m container::

    docker run \
      --interactive --tty --rm \
      --volume="/tmp/demo/transfers:/tmp/demo/transfers" \
      --volume="/tmp/demo/completed:/home/a3m/.local/share/a3m/share/completed" \
      --entrypoint=python \
      ghcr.io/artefactual-labs/a3m:main \
      -m a3m.cli.client --name=transfer1 file:///tmp/demo/transfers/transfer1
    AIP f733d3e8-cede-4e9c-93ee-5728b32f0b7b is being generated...

Success! You can find the AIP under::

    /tmp/demo/completed/transfer1-f733d3e8-cede-4e9c-93ee-5728b32f0b7b.7z

Client and server in separate containers
========================================

This section shows the client-server mode. We are going to create a Docker
network so our server and client can talk to each other.

Create the virtual network::

    docker network create a3m-network

Run the gRPC server in detached mode listening locally on port ``7000``::

    docker run --rm --network a3m-network --name a3md --detach --publish 7000:7000 \
        ghcr.io/artefactual-labs/a3m:main

Submit a new transfer using the gRPC client::

    docker run --rm --network a3m-network --name a3mc --interactive --tty --entrypoint=python \
        ghcr.io/artefactual-labs/a3m:main \
            -m a3m.cli.client --address=a3md:7000 \
                https://github.com/artefactual/archivematica-sampledata/raw/master/SampleTransfers/ZippedDirectoryTransfers/DemoTransferCSV.zip

We have produced an AIP that is stored inside the `a3md` container. The previous
demo in this document shows how we can use Docker volumes to retrieve the AIP.

Don't forget to clean up before leaving::

    docker stop a3md
    docker network remove a3m-network

.. note::

   Remember that when ``--address`` is not included, ``a3m.cli.client`` embeds
   its own instance of the a3m server, i.e. you do not need to run the server
   separately.


Custom images
=============

Our image ``ghcr.io/artefactual-labs/a3m`` can be used as a parent image. Say
you're building a new application embedding a3m and you need a few extra
dependencies installed. Instead of building a new image from scratch, you can
base your image on ours.

For demonstration purposes, we're going to add a new set of self-signed
certificates issued by a local CA. This is all managed by a tool called
``mkcert`` that we're going to install.

.. literalinclude:: ../examples/Dockerfile

Let's build it and run it::

    docker build -f Dockerfile -t a3m-webapp:latest
    docker run --rm a3m-webapp:latest

That's all. You're now running a new Python application embedding a3m. It was
just an example, but the possibilities are endless! Refer to Docker's
documentation to know more about this technique.
