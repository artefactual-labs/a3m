[![Travis CI](https://travis-ci.org/sevein/a3m.svg?branch=main)](https://travis-ci.org/sevein/a3m)

## a3m

See the [tasklist](https://www.notion.so/a3m-acfaae80a800407b80317b7efd3b76bf) for more details.

- [Usage](#usage)
- [Development](#development)

### Usage

<details>
<summary>Command-line interface</summary>

`a3m.server.rpc.client` is work in progress - used mostly for local testing. The following are examples that connect to the server listening on the Compose development environment.

Submit a new transfer:

    python -m a3m.server.rpc.client submit --address=127.0.0.1:52000 https://github.com/artefactual/archivematica-sampledata/raw/master/SampleTransfers/ZippedBag.zip

Look up processing status of a transfer:

    python -m a3m.server.rpc.client status --address=127.0.0.1:52000 f81eff9f-312d-4eb3-9b4f-75fbb4474780

</details>

### Development

a3m depends on many open-source tools that need to be available in the system path. Docker Compose sets up an environment with all these dependencies available. However, it is also possible to keep Docker out of your development workflow.

<details>
<summary>Docker Compose</summary>

Try the following if you feel confortable using our Makefile:

    make create-volume build bootstrap restart

Otherwise, follow these steps:

    # Create the external data volume
    mkdir -p hack/compose-volume
    docker volume create --opt type=none --opt o=bind --opt device=./hack/compose-volume a3m-pipeline-data

    # Build service
    env COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose build

    # Create database
    docker-compose run --rm --no-deps --entrypoint /a3m/manage.py a3m migrate --noinput

    # Bring the service up
    docker-compose up -d a3m

You're ready to submit a transfer:

    # Submit a transfer
    docker-compose run --rm --entrypoint sh a3m -c "python -m a3m.server.rpc.client submit --address=a3m:7000 https://github.com/artefactual/archivematica-sampledata/raw/master/SampleTransfers/ZippedBag.zip"

    # Find the AIP generated
    find hack/compose-volume -name "*.7z";

</details>

<details>
<summary>Container-free workflow</summary>

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
    pytest -p no:warnings

    # Populate the internal database:
    ./manage.py migrate

    # Run a3m server:
    python -m a3m

Start a new transfer:

    $ python -m a3m.server.rpc.client submit https://github.com/artefactual/archivematica-sampledata/raw/master/SampleTransfers/ZippedBag.zip
    Submitting...
    Transfer created: 0f667867-800a-466f-856f-fea5980f1d97

You can find both the database and the shared directory under `~/.local/share/a3m/`.

</details>
