======
Docker
======

Our Docker image  is extremely convenient because it includes many software
dependencies that you would need to install manually otherwise. This document
exemplifies how to run a3m in a container environment using the Docker
command-line interface.

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

   Remember that when ``--address`` is not including, ``a3m.cli.client`` embeds
   its own instance of the a3m server, i.e. you do not need to run the server
   separately.
