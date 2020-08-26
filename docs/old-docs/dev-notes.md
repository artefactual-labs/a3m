# Development

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
you will have to ensure they're available manually.

a3m needs Python 3.8 or newer. So for an Ubuntu/Debian Linux environment:

    sudo apt install -y python3.8 python3.8-venv python3.8-dev

Check out this repository:

    git clone --depth 1 https://github.com/artefactual-labs/a3m.git

Then follow these steps:

    # Create virtual environment and activate it
    virtualenv --python=python3.8 .venv
    source .venv/bin/activate

    # Install the dependencies
    pip install -r requirements-dev.txt

    # Run the tests:
    pytest

    # Run a3m server
    python -m a3m.cli.server

Start a new transfer:

    python -m a3m.cli.client --address=127.0.0.1:7000 --name=demo https://github.com/artefactual/archivematica-sampledata/raw/master/SampleTransfers/ZippedDirectoryTransfers/DemoTransferCSV.zip

You can find both the database and the shared directory under `~/.local/share/a3m/`.

</details>

Other things you can do:

<details>

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
