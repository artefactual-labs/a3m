<p align="left">
  <a href="https://github.com/artefactual-labs/a3m/releases/latest"><img src="https://img.shields.io/github/v/release/artefactual-labs/a3m.svg?color=orange"/></a>
  <img src="https://github.com/artefactual-labs/a3m/workflows/Tests/badge.svg"/>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/evercam/evercam-dashboard"/></a>
  <a href="https://codecov.io/gh/artefactual-labs/a3m"><img src="https://img.shields.io/codecov/c/github/artefactual-labs/a3m"/></a>
  <a href="https://pyup.io/repos/github/artefactual-labs/a3m/"><img src="https://pyup.io/repos/github/artefactual-labs/a3m/shield.svg" alt="Updates" /></a>
</p>

## a3m

- [Usage](#usage)
- [Development](#development)

### Usage

Most of the use cases that we envision for a3m include the use of our Docker image because it includes all the tools and dependencies needed. It is possible to run a3m without Docker as long as you have Python, but a3m does not know how to install software dependencies for you automatically, e.g. 7-zip, ffmpeg, unar...

<details>

<summary>gRPC server</summary>
<hr/>

The following example shows how to set up a gRPC server and a client sharing the same network using Docker. Alternatively, see our [screencast](https://asciinema.org/a/lKWDIxPSwSfDySxTIgPPlYZrU).

Create a virtual network:

    docker network create a3m-network

The following command will run the gRPC server in detached mode listening locally on port 7000:

    docker run --rm --detach --name a3m --network a3m-network -p 7000:7000 docker.pkg.github.com/artefactual-labs/a3m/a3m:main

Submit a transfer with the gRPC client, e.g.:

    docker run --rm --network a3m-network --entrypoint=python docker.pkg.github.com/artefactual-labs/a3m/a3m:main -m a3m.server.rpc.client submit --wait --address=a3m:7000 https://github.com/artefactual/archivematica-sampledata/raw/master/SampleTransfers/ZippedDirectoryTransfers/DemoTransferCSV.zip

Using our [service definition](https://github.com/artefactual-labs/a3m/blob/main/a3m/server/rpc/a3m.proto), it is possible to generate client-side code in multiple programming languages. See [gRPC concepts](https://grpc.io/docs/guides/concepts/) for more.

Don't forget to clean up before leaving!

    docker stop a3m
    docker network remove a3m-network

</details>

<details>

<summary>Enduro activity worker</summary>
<hr/>

This mode is work in progress (see [#40](https://github.com/artefactual-labs/a3m/issues/40) for more).

    docker run --rm --env="A3M_CADENCE_SERVER=127.0.0.1:12345" docker.pkg.github.com/artefactual-labs/a3m/a3m:main --mode="enduro"

</details>

<details>

<summary>Embedded API</summary>
<hr />

Python developers should be able to implement new solutions embedding a3m as a library. See [#42](https://github.com/artefactual-labs/a3m/issues/42) for more.

```python
import a3m

runner = a3m.Runner()
runner.submit_package("https://...", wait=True)
```

</details>

### Development

It is possible to do local development work in a3m. But we also provide an
environment based on Docker Compose with all the tools and dependencies
installed so you don't have to run them locally.

<details>

<summary>Docker Compose</summary>
<hr>

Try the following if you feel confortable using our Makefile:

    make create-volume build bootstrap restart

Otherwise, follow these steps:

    # Create the external data volume
    mkdir -p hack/compose-volume
    docker volume create --opt type=none --opt o=bind --opt device=./hack/compose-volume a3m-pipeline-data

    # Build service
    env COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose build

    # Bring the service up
    docker-compose up -d a3m

You're ready to submit a transfer:

    # Submit a transfer
    docker-compose run --rm --entrypoint sh a3m -c "python -m a3m.server.rpc.client submit --wait --address=a3m:7000 https://github.com/artefactual/archivematica-sampledata/raw/master/SampleTransfers/ZippedDirectoryTransfers/DemoTransferCSV.zip"

    # Find the AIP generated
    find hack/compose-volume -name "*.7z";

</details>

<details>

<summary>Container-free workflow</summary>
<hr>

Be aware that a3m has application dependencies that need to be available in the
system path. The Docker image makes them all available while in this workflow
you may have to ensure they're available manually.

Start checking out this repository and follow these steps:

    # Create virtual environment and activate it
    python -m venv .venv
    source .venv/bin/activate

    # Install the dependencies
    pip install -r requirements-dev.txt

    # Run the tests:
    pytest

    # Run a3m server
    python -m a3m

Start a new transfer:

    $ python -m a3m.server.rpc.client submit --wait https://github.com/artefactual/archivematica-sampledata/raw/master/SampleTransfers/ZippedDirectoryTransfers/DemoTransferCSV.zip
    Submitting...
    Transfer created: 0f667867-800a-466f-856f-fea5980f1d97

You can find both the database and the shared directory under `~/.local/share/a3m/`.

</details>

Other things you can do:

<details>

<summary>Python debugging with pdb</summary>
<hr>

Stop a3m if it's already running:

    docker-compose stop a3m

Introduce a [breakpoint](https://docs.python.org/3/library/functions.html#breakpoint)
in the code. Breakpoints can be used anywhere, including client modules.

    breakpoint()  # Add this!
    important_code()

Run a3m as follows:

    docker-compose run --rm --publish=52000:7000 a3m

The [debugger](https://docs.python.org/3/library/pdb.html) should activate as
your breakpoint is reached. Use commands to control the debugger, e.g. `help`.

</details>

<details>

<summary>Enable the debug mode</summary>
<hr>

a3m comes with a pre-configured logger that hides events with level `INFO` or
lower. `INFO` is bloated, so we use `WARNING` and higher.

Set the `A3M_DEBUG` environment string to see all events. The string can be
injected in several ways, e.g.:

    docker-compose run --rm -e A3M_DEBUG=yes --publish=52000:7000 a3m

The logging configuration lives in `a3m.settings.common`.

</details>
