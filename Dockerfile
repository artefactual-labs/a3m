ARG SYSTEM_IMAGE=ubuntu:22.04

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
	&& add-apt-repository --no-update --yes "deb [arch=amd64] http://packages.archivematica.org/1.15.x/ubuntu-externals jammy main" \
	&& add-apt-repository --no-update --yes "deb http://archive.ubuntu.com/ubuntu/ jammy multiverse" \
	&& add-apt-repository --no-update --yes "deb http://archive.ubuntu.com/ubuntu/ jammy-security universe" \
	&& add-apt-repository --no-update --yes "deb http://archive.ubuntu.com/ubuntu/ jammy-updates multiverse" \
	&& curl -so /tmp/repo-mediaarea_1.0-21_all.deb -L https://mediaarea.net/repo/deb/repo-mediaarea_1.0-21_all.deb \
	&& dpkg -i /tmp/repo-mediaarea_1.0-21_all.deb \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
	atool \
	bulk-extractor \
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

# Python build.
RUN set -ex \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
	build-essential \
	libbz2-dev \
	libffi-dev \
	liblzma-dev \
	libncursesw5-dev \
	libreadline-dev \
	libsqlite3-dev \
	libssl-dev \
	libxml2-dev \
	libxmlsec1-dev \
	tk-dev \
	xz-utils \
	zlib1g-dev

# Create a3m user
RUN set -ex \
	&& groupadd --gid ${GROUP_ID} --system a3m \
	&& useradd --uid ${USER_ID} --gid ${GROUP_ID} --create-home --home-dir /home/a3m --system a3m \
	&& mkdir -p /home/a3m/.local/share/a3m/share \
	&& chown -R a3m:a3m /home/a3m/.local


#
# a3m
#

FROM base AS a3m

COPY ./a3m/externals/fido/ /usr/lib/archivematica/archivematicaCommon/externals/fido/
COPY ./a3m/externals/fiwalk_plugins/ /usr/lib/archivematica/archivematicaCommon/externals/fiwalk_plugins/

USER a3m

ARG DJANGO_SETTINGS_MODULE=a3m.settings.common
ENV DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}
ENV PYENV_ROOT="/home/a3m/.pyenv"
ENV PATH=$PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH
ARG PYTHON_VERSION=3.9.18
ARG REQUIREMENTS=/a3m/requirements-dev.txt

RUN set -ex \
	&& curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash \
	&& pyenv install ${PYTHON_VERSION} \
	&& pyenv global ${PYTHON_VERSION}

COPY ./requirements.txt /a3m/requirements.txt
COPY ./requirements-dev.txt /a3m/requirements-dev.txt
RUN set -ex \
	&& pyenv exec python3 -m pip install --upgrade pip setuptools \
	&& pyenv exec python3 -m pip install --requirement ${REQUIREMENTS} \
	&& pyenv rehash

COPY . /a3m
WORKDIR /a3m

ENTRYPOINT ["python", "-m", "a3m.cli.server"]
