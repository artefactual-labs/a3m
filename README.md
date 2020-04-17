[![Travis CI](https://travis-ci.org/sevein/a3m.svg?branch=main)](https://travis-ci.org/sevein/a3m)

## a3m

See the [tasklist](https://www.notion.so/a3m-acfaae80a800407b80317b7efd3b76bf) for more details.

- [Usage](#usage)
- [Development](#development)
  - [Container-free workflow](#container-free-workflow)
  - [Docker Compose](#docker-compose)

### Usage

    Work in progress!

### Development

#### Container-free workflow

There are a few limitations that we will address in the future:

- You need to create `/var/archivematica` and have write access, and
- Preservation tasks need to be locally available for a fully working experience, and
- Python 2 needed.

Check out the repo and create the virtual environment from inside:

    virtualenv --python=python2 .venv

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

#### Docker Compose

Start with the following:

    make create-volumes build bootstrap restart
