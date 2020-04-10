.DEFAULT_GOAL := help

# Paths for Docker named volumes
AM_PIPELINE_DATA ?= $(HOME)/.a3m/am-pipeline-data
SS_LOCATION_DATA ?= $(HOME)/.a3m/ss-location-data


define compose_amauat
	docker-compose -f docker-compose.yml -f docker-compose.acceptance-tests.yml $(1)
endef


build:
	env COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose build  # --progress plain --parallel
	env COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose up -d

create-volumes:  ## Create external data volumes.
	mkdir -p ${AM_PIPELINE_DATA}
	docker volume create \
		--opt type=none \
		--opt o=bind \
		--opt device=$(AM_PIPELINE_DATA) \
			am-pipeline-data
	mkdir -p ${SS_LOCATION_DATA}
	docker volume create \
		--opt type=none \
		--opt o=bind \
		--opt device=$(SS_LOCATION_DATA) \
			ss-location-data

bootstrap: bootstrap-storage-service bootstrap-a3m-db  ## Full bootstrap.

bootstrap-storage-service:  ## Boostrap Storage Service (new database).
	docker-compose exec mysql mysql -hlocalhost -uroot -p12345 -e "\
		DROP DATABASE IF EXISTS SS; \
		CREATE DATABASE SS; \
		GRANT ALL ON SS.* TO 'archivematica'@'%' IDENTIFIED BY 'demo';"
	docker-compose run \
		--rm \
		--entrypoint /src/storage_service/manage.py \
			archivematica-storage-service \
				migrate --noinput
	docker-compose run \
		--rm \
		--entrypoint /src/storage_service/manage.py \
			archivematica-storage-service \
				create_user \
					--username="test" \
					--password="test" \
					--email="test@test.com" \
					--api-key="test" \
					--superuser
	# SS needs to be restarted so the local space is created.
	# See #303 (https://git.io/vNKlM) for more details.
	docker-compose restart archivematica-storage-service

manage-a3m:  ## Run Django /manage.py on a3m, suppling <command> [options] as value to ARG, e.g., `make manage-a3m ARG=shell`
	docker-compose run \
		--rm \
		--entrypoint /a3m/manage.py \
			archivematica-mcp-server \
				$(ARG)

manage-ss:  ## Run Django /manage.py on Storage Service, suppling <command> [options] as value to ARG, e.g., `make manage-ss ARG='shell --help'`
	docker-compose run \
		--rm \
		--entrypoint /src/storage_service/manage.py \
			archivematica-storage-service \
				$(ARG)

bootstrap-a3m-db:  ## Bootstrap a3m (new database).
	docker-compose exec mysql mysql -hlocalhost -uroot -p12345 -e "\
		DROP DATABASE IF EXISTS MCP; \
		CREATE DATABASE MCP; \
		GRANT ALL ON MCP.* TO 'archivematica'@'%' IDENTIFIED BY 'demo';"
	docker-compose run \
		--rm \
		--entrypoint /a3m/manage.py \
			archivematica-mcp-server \
				migrate --noinput
	docker-compose run \
		--rm \
		--entrypoint /a3m/manage.py \
			archivematica-mcp-server \
				install \
					--username="test" \
					--password="test" \
					--email="test@test.com" \
					--org-name="test" \
					--org-id="test" \
					--api-key="test" \
					--ss-url="http://archivematica-storage-service:8000" \
					--ss-user="test" \
					--ss-api-key="test" \
					--site-url="http://archivematica-dashboard:8000"

restart:
	docker-compose restart archivematica-mcp-server
	docker-compose restart archivematica-mcp-client

restart-all: restart  ## Restart Archivematica services: MCPServer, MCPClient and Storage Service.
	docker-compose restart archivematica-storage-service

compile-requirements:  ## Run pip-compile
	pip-compile --output-file requirements.txt requirements.in
	pip-compile --output-file requirements-dev.txt requirements-dev.in

db:  ## Connect to the MySQL server using the CLI.
	docker-compose exec mysql mysql -hlocalhost -uroot -p12345

flush: flush-shared-dir bootstrap restart-am-services  ## Delete ALL user data.

flush-shared-dir-mcp-configs:  ## Delete processing configurations - it restarts MCPServer.
	rm -f ${AM_PIPELINE_DATA}/sharedMicroServiceTasksConfigs/processingMCPConfigs/defaultProcessingMCP.xml
	rm -f ${AM_PIPELINE_DATA}/sharedMicroServiceTasksConfigs/processingMCPConfigs/automatedProcessingMCP.xml
	docker-compose restart archivematica-mcp-server

flush-shared-dir:  ## Delete contents of the shared directory data volume.
	rm -rf ${AM_PIPELINE_DATA}/*

flush-logs:  ## Delete container logs - requires root privileges.
	@./helpers/flush-docker-logs.sh

flush-test-dbs:
	docker-compose exec mysql mysql -hlocalhost -uroot -p12345 -e "DROP DATABASE IF EXISTS test_MCP; DROP DATABASE IF EXISTS test_SS;"

test-all: test-mcp-server test-mcp-client test-storage-service  ## Run all tests.

test-a3m:  ## Run a3m tests.
	echo "TODO"

test-storage-service:  ## Run Storage Service tests.
	docker-compose run --workdir /src --rm --no-deps --entrypoint py.test -e "DJANGO_SETTINGS_MODULE=storage_service.settings.test" archivematica-storage-service -p no:cacheprovider --reuse-db -v

help:  ## Print this help message.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
