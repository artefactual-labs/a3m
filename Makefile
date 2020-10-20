.DEFAULT_GOAL := help

A3M_PIPELINE_DATA ?= $(CURDIR)/hack/compose-volume

CURRENT_UID := $(shell id -u)


shell:  ## Open a shell in a new container.
	docker-compose run --rm --entrypoint bash a3m

build:  ## Build and recreate containers.
	env COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose build
	env COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose up -d --force-recreate

create-volume:  ## Create external data volume.
	mkdir -p ${A3M_PIPELINE_DATA}
	docker volume create \
		--opt type=none \
		--opt o=bind \
		--opt device=$(A3M_PIPELINE_DATA) \
			a3m-pipeline-data

migrate: bootstrap  ## Same as make bootstrap.

bootstrap:  ## Bootstrap a3m (new database).
	docker-compose run --rm --no-deps --entrypoint /a3m/manage.py a3m migrate --noinput

manage:  ## Run Django /manage.py on a3m, suppling <command> [options] as value to ARG, e.g., `make manage ARG=shell`
	docker-compose run --rm --no-deps --entrypoint /a3m/manage.py a3m $(ARG)

migrations:  ## Make Django migrations.
	docker-compose run --rm --user=$(CURRENT_UID) --entrypoint=/a3m/manage.py a3m makemigrations main fpr

reset-migrations:
	@echo "Disabled! This is a temporary hack, uncomment and use carefully!"
	exit 1
	find a3m/main/migrations -name "*.py" -delete
	find a3m/fpr/migrations -name "*.py" -delete
	find a3m/ -name "*.pyc" -delete
	docker-compose run --rm --user=$(CURRENT_UID) --entrypoint=/a3m/manage.py a3m makemigrations main fpr
	git checkout -- a3m/main/migrations/0002_initial_data.py a3m/fpr/migrations/0002_initial_data.py
	black a3m/main/migrations a3m/fpr/migrations
	reorder-python-imports --exit-zero-even-if-changed a3m/main/migrations/0001_initial.py a3m/fpr/migrations/0001_initial.py
	pyupgrade --py38-plus --exit-zero-even-if-changed a3m/main/migrations/0001_initial.py a3m/fpr/migrations/0001_initial.py

logs:
	docker-compose logs -f

restart:  ## Restart services
	docker-compose restart a3m

pip-compile:  # Compile pip requirements
	pip-compile --output-file requirements.txt requirements.in
	pip-compile --output-file requirements-dev.txt requirements-dev.in

pip-upgrade:  # Upgrade pip requirements
	pip-compile --upgrade --output-file requirements.txt requirements.in
	pip-compile --upgrade --output-file requirements-dev.txt requirements-dev.in

pip-sync:  # Sync virtualenv
	pip-sync requirements-dev.txt

pip-ensure:  # Compile, upgrade and install requirements
	$(MAKE) pip-upgrade pip-sync
	pip list --outdated

db:
	sqlite3 $(CURDIR)/hack/compose-volume/db.sqlite

flush: flush-db flush-shared-dir bootstrap restart  ## Delete ALL user data.

flush-db:  ## Flush SQLite database.
	docker-compose run --rm --no-deps --entrypoint sh a3m -c "rm -rf /home/a3m/.local/share/a3m/db.sqlite"

flush-shared-dir:  ## Flush shared directory including the database.
	docker-compose run --rm --no-deps --entrypoint sh a3m -c "rm -rf /home/a3m/.local/share/a3m/share/"

amflow:  ## See workflow.
	amflow edit --file=a3m/assets/workflow.json

protoc:  ## Generate gRPC code.
	python3 -m grpc_tools.protoc -I=. --python_out=. --grpc_python_out=. a3m/server/rpc/proto/a3m.proto
	black $(CURDIR)/a3m/server/rpc/proto

help:  ## Print this help message.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

publish: publish-clean  ## Publish to PyPI
	pip install --upgrade twine wheel
	python setup.py sdist
	python setup.py bdist_wheel --universal
	twine check dist/*
	twine upload dist/* --repository-url https://upload.pypi.org/legacy/

publish-clean:
	rm -rf a3m.egg-info/
	rm -rf build/
	rm -rf dist/
