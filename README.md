[![Travis CI](https://travis-ci.org/sevein/a3m.svg?branch=main)](https://travis-ci.org/sevein/a3m)

## a3m

See the [tasklist](https://www.notion.so/a3m-acfaae80a800407b80317b7efd3b76bf) for more details.

- [Usage](#usage)
- [Development](#development)

### Usage

<details>

<summary>Command-line interface</summary>
<hr>

`a3m.server.rpc.client` is work in progress - used mostly for local testing. The following are examples that connect to the server listening on the Compose development environment.

Submit a new transfer:

    python -m a3m.server.rpc.client submit --wait --address=127.0.0.1:52000 https://github.com/artefactual/archivematica-sampledata/raw/master/SampleTransfers/ZippedDirectoryTransfers/DemoTransferCSV.zip

Look up processing status of a transfer:

    python -m a3m.server.rpc.client status --address=127.0.0.1:52000 f81eff9f-312d-4eb3-9b4f-75fbb4474780

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
