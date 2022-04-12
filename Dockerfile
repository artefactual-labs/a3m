ARG SYSTEM_IMAGE=ubuntu:18.04

#
# Base
#

FROM ${SYSTEM_IMAGE} AS base

ARG USER_ID=1000
ARG GROUP_ID=1000

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
	&& add-apt-repository --no-update --yes "deb [arch=amd64] http://packages.archivematica.org/1.13.x/ubuntu-externals bionic main" \
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
		openjdk-8-jre-headless \
		p7zip-full \
		pbzip2 \
		pst-utils \
		rsync \
		sleuthkit \
		sqlite3 \
		tesseract-ocr \
		tree \
		unar \
		unrar-free \
		uuid \
	&& rm -rf /var/lib/apt/lists/*

# Download ClamAV virus signatures
RUN freshclam --quiet

# Create a3m user
RUN set -ex \
	&& groupadd --gid ${GROUP_ID} --system a3m \
	&& useradd --uid ${USER_ID} --gid ${GROUP_ID} --create-home --home-dir /home/a3m --system a3m \
	&& mkdir -p /home/a3m/.local/share/a3m \
	&& chown -R a3m:a3m /home/a3m/.local


#
# a3m
#

FROM base AS a3m

ARG PYTHON_VERSION=3.9
ARG REQUIREMENTS=/a3m/requirements-dev.txt
ARG DJANGO_SETTINGS_MODULE=a3m.settings.common
ENV DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}
ENV PATH=/home/a3m/.local/a3m-venv/bin:$PATH

COPY ./a3m/externals/fido/ /usr/lib/archivematica/archivematicaCommon/externals/fido/
COPY ./a3m/externals/fiwalk_plugins/ /usr/lib/archivematica/archivematicaCommon/externals/fiwalk_plugins/

RUN set -ex \
	&& add-apt-repository ppa:deadsnakes/ppa \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		build-essential \
		python${PYTHON_VERSION} \
		python${PYTHON_VERSION}-venv \
		python${PYTHON_VERSION}-distutils \
		libpython${PYTHON_VERSION}-dev \
	&& update-alternatives --install /usr/bin/python python /usr/bin/python${PYTHON_VERSION} 1 \
	&& update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1 \
	&& rm -rf /var/lib/apt/lists/*

USER a3m

COPY ./requirements.txt /a3m/requirements.txt
COPY ./requirements-dev.txt /a3m/requirements-dev.txt
RUN set -ex \
	&& python -m venv /home/a3m/.local/a3m-venv \
	&& pip install --upgrade pip \
	&& pip install --no-cache-dir -r ${REQUIREMENTS}

COPY . /a3m
WORKDIR /a3m

ENTRYPOINT ["python", "-m", "a3m.cli.server"]
