======
Docker
======

Our Docker image is extremely convenient because it includes many software
dependencies that you would need to install manually otherwise.

Using our Docker image
======================

Off the shelf, the Docker image brings an environment with a3m and its
dependencies installed and ready to use. Below is an example of using the
client-server mode provided by a3m using the Docker command-line interface.

Create a virtual network so our communicate can communicate with each other::

    docker network create a3m-network

Download the latest a3m Docker image::

    docker pull ghcr.io/artefactual-labs/a3m:main

The following command will run the gRPC server in detached mode listening locally on port ``7000``::

    docker run --rm --network a3m-network --name a3md --detach --publish 7000:7000 \
        ghcr.io/artefactual-labs/a3m:main

This is going to use the gRPC client to submit a new tranfser::

    docker run --rm --network a3m-network --name a3mc --interactive --tty --entrypoint=python \
        ghcr.io/artefactual-labs/a3m:main \
            -m a3m.cli.client --address=a3md:7000 \
                https://github.com/artefactual/archivematica-sampledata/raw/master/SampleTransfers/ZippedDirectoryTransfers/DemoTransferCSV.zip

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
