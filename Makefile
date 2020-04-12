.DEFAULT_GOAL := help

A3M_PIPELINE_DATA ?= $(HOME)/.a3m/am-pipeline-data

define compose_amauat
	docker-compose -f docker-compose.yml -f docker-compose.acceptance-tests.yml $(1)
endef

build:
	env COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose build
	env COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose up -d --force-recreate

create-volumes:  ## Create external data volumes.
	mkdir -p ${A3M_PIPELINE_DATA}
	docker volume create \
		--opt type=none \
		--opt o=bind \
		--opt device=$(A3M_PIPELINE_DATA) \
			a3m-pipeline-data

bootstrap:  ## Bootstrap a3m (new database).
	docker-compose exec mysql mysql -hlocalhost -uroot -p12345 -e "\
		DROP DATABASE IF EXISTS MCP; \
		CREATE DATABASE MCP; \
		GRANT ALL ON MCP.* TO 'archivematica'@'%' IDENTIFIED BY 'demo';"
	docker-compose run \
		--rm \
		--entrypoint /a3m/manage.py \
			archivematica-mcp-server \
				migrate --noinput

manage:  ## Run Django /manage.py on a3m, suppling <command> [options] as value to ARG, e.g., `make manage-a3m ARG=shell`
	docker-compose run \
		--rm \
		--entrypoint /a3m/manage.py \
			archivematica-mcp-server \
				$(ARG)

migrations:
	docker-compose run --rm --user=1000 --entrypoint=/a3m/manage.py archivematica-mcp-server makemigrations main

restart:  # Restart services
	docker-compose restart archivematica-mcp-server
	docker-compose restart archivematica-mcp-client

compile-requirements:  ## Run pip-compile
	pip-compile --output-file requirements.txt requirements.in
	pip-compile --output-file requirements-dev.txt requirements-dev.in

db:  ## Connect to the MySQL server using the CLI.
	docker-compose exec mysql mysql -hlocalhost -uroot -p12345

flush: flush-shared-dir bootstrap  ## Delete ALL user data.

flush-shared-dir-mcp-configs:  ## Delete processing configurations - it restarts MCPServer.
	rm -f ${A3M_PIPELINE_DATA}/sharedMicroServiceTasksConfigs/processingMCPConfigs/defaultProcessingMCP.xml
	rm -f ${A3M_PIPELINE_DATA}/sharedMicroServiceTasksConfigs/processingMCPConfigs/automatedProcessingMCP.xml
	docker-compose restart archivematica-mcp-server

flush-shared-dir:  ## Delete contents of the shared directory data volume.
	rm -rf ${A3M_PIPELINE_DATA}/*

flush-logs:  ## Delete container logs - requires root privileges.
	@./helpers/flush-docker-logs.sh

flush-test-dbs:
	docker-compose exec mysql mysql -hlocalhost -uroot -p12345 -e "DROP DATABASE IF EXISTS test_MCP; DROP DATABASE IF EXISTS test_SS;"

test-all: test-mcp-server test-mcp-client  ## Run all tests.

test-a3m:  ## Run a3m tests.
	echo "TODO"

help:  ## Print this help message.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
