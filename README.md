[![Travis CI](https://travis-ci.org/sevein/a3m.svg?branch=main)](https://travis-ci.org/sevein/a3m)

## a3m

See the [tasklist](https://www.notion.so/a3m-acfaae80a800407b80317b7efd3b76bf) for more details.

- [Usage](#usage)
- [Development](#development)

### Usage

    Work in progress!

### Development

a3m depends on many open-source tools that need to be available in the system path. Docker Compose sets up an environment with all these dependencies available. However, it is also possible to keep Docker out of your development workflow.

<details>
<summary>Docker Compose</summary>

If you're confortable using our Makefile try:

    make create-volumes build bootstrap restart

Otherwise...

    # Build service
    env COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose build

    # Create database
    docker-compose run --rm --no-deps --entrypoint /a3m/manage.py a3m migrate --noinput

    # Bring the service up
    docker-compose up -d a3m

    # Submit a transfer
    docker-compose run --rm --entrypoint sh a3m -c "python -m a3m.server.rpc.client a3m:7000"

    # Check out the AIP
    sudo find ~/.a3m/a3m-pipeline-data/currentlyProcessing/ -name "*.7z";

</details>

<details>
<summary>Container-free workflow</summary>

There are a couple limitations that we will address in the future:

- You need to create `/var/archivematica` and have write access, and
- Preservation tasks need to be locally available for a fully working experience, and

Check out the repo and create the virtual environment from inside:

    python -m venv .venv

Enable the environment:

    source .venv/bin/activate

Install the dependencies:

    pip install -r requirements-dev.txt

Run the tests:

    pytest -p no:warnings

Let's run a3m. We need to create the shared directory:

    sudo mkdir -p /var/archivematica/sharedDirectory
    sudo chown -R $(id -u):$(id -g) /var/archivematica

Populate the database (we're using SQLite):

    ./manage.py migrate

Run a3m server:

    env A3M_RPC_BIND_ADDRESS=127.0.0.1:7000 python -m a3m

Start a new transfer:

    $ python -m a3m.server.rpc.client 127.0.0.1:7000
    Transfer created: afe8898c-a194-42ce-84de-4021f2795fb2
    Done!

</details>
