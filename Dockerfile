ARG SYSTEM_IMAGE=ubuntu:18.04
ARG TARGET=archivematica

#
# Base
#

FROM ${SYSTEM_IMAGE} AS base

ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED 1

RUN set -ex \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		apt-transport-https \
		curl \
		git \
		gpg-agent \
		locales \
		locales-all \
		software-properties-common \
	&& rm -rf /var/lib/apt/lists/*

# Set the locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# OS dependencies
RUN set -ex \
	&& curl -s https://packages.archivematica.org/GPG-KEY-archivematica | apt-key add - \
	&& add-apt-repository --no-update --yes "deb [arch=amd64] http://packages.archivematica.org/1.11.x/ubuntu-externals bionic main" \
	&& add-apt-repository --no-update --yes "deb http://archive.ubuntu.com/ubuntu/ bionic multiverse" \
	&& add-apt-repository --no-update --yes "deb http://archive.ubuntu.com/ubuntu/ bionic-security universe" \
	&& add-apt-repository --no-update --yes "deb http://archive.ubuntu.com/ubuntu/ bionic-updates multiverse" \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		atool \
		bulk-extractor \
		clamav \
		ffmpeg \
		ghostscript \
		coreutils \
		libavcodec-extra \
		imagemagick \
		inkscape \
		jhove \
		libimage-exiftool-perl \
		libevent-dev \
		libjansson4 \
		mediainfo \
		mediaconch \
		nailgun \
		openjdk-8-jre-headless \
		p7zip-full \
		pbzip2 \
		pst-utils \
		rsync \
		siegfried \
		sleuthkit \
		tesseract-ocr \
		tree \
		ufraw \
		unar \
		unrar-free \
		uuid \
	&& rm -rf /var/lib/apt/lists/*

# Download ClamAV virus signatures
# ############################## RUN freshclam --quiet

# Create Archivematica user
RUN set -ex \
	&& groupadd --gid 333 --system archivematica \
	&& useradd --uid 333 --gid 333 --create-home --system archivematica \
	&& mkdir -p /var/archivematica/sharedDirectory \
	&& chown -R archivematica:archivematica /var/archivematica


#
# Archivematica
#

FROM base AS archivematica

ARG REQUIREMENTS=/a3m/requirements-dev.txt

RUN set -ex \
	&& curl -s https://bootstrap.pypa.io/get-pip.py | python \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		build-essential \
		python-dev \
		libmysqlclient-dev \
		libffi-dev \
		libyaml-dev \
		libssl-dev \
		libxml2-dev \
		libxslt-dev \
	&& rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /a3m/requirements.txt
COPY ./requirements-dev.txt /a3m/requirements-dev.txt
RUN pip install -r ${REQUIREMENTS}

COPY . /a3m
WORKDIR /a3m

USER archivematica

ENV DJANGO_SETTINGS_MODULE a3m.settings.common

ENTRYPOINT ["python", "-m", "a3m"]


#
# MCPServer
#

FROM archivematica as archivematica-mcp-server

ENTRYPOINT ["python", "-m", "a3m", "server"]


#
# MCPClient
#

FROM archivematica as archivematica-mcp-client

COPY ./a3m/externals/fido/ /usr/lib/archivematica/archivematicaCommon/externals/fido/
COPY ./a3m/externals/fiwalk_plugins/ /usr/lib/archivematica/archivematicaCommon/externals/fiwalk_plugins/

ENTRYPOINT ["python", "-m", "a3m", "client"]


#
# Target
#

FROM ${TARGET}
