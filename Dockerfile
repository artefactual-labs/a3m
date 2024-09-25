# syntax=docker/dockerfile:1.10.0-labs

ARG SYSTEM_IMAGE=ubuntu:22.04
ARG UV_VERSION=0.4.16
ARG USER_ID=1000
ARG GROUP_ID=1000

#
# Base
#

FROM ${SYSTEM_IMAGE} AS base

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

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
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

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

# -----------------------------------------------------------------------------

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# -----------------------------------------------------------------------------

FROM base AS a3m

ARG USER_ID
ARG GROUP_ID

# Create a3m user.
RUN set -ex \
	&& groupadd --gid ${GROUP_ID} --system a3m \
	&& useradd --uid ${USER_ID} --gid ${GROUP_ID} --home-dir /home/a3m --system a3m \
	&& mkdir -p /home/a3m/.local/share/a3m/share \
	&& chown -R a3m:a3m /home/a3m

# Install uv.
COPY --from=uv /uv /bin/uv

# Enable bytecode compilation.
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume.
ENV UV_LINK_MODE=copy

# Change the current user.
USER a3m

# Install the project into `/app`.
WORKDIR /app

# Install the project's dependencies using the lockfile and settings.
RUN --mount=type=cache,target=/home/a3m/.cache/uv,uid=${USER_ID},gid=${GROUP_ID} \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Add the rest of the project source code and install it.
# Installing separately from its dependencies allows optimal layer caching.
COPY --exclude=.git . /app
RUN --mount=type=cache,target=/home/a3m/.cache/uv,uid=${USER_ID},gid=${GROUP_ID} \
	--mount=type=bind,source=.git,target=.git \
    uv sync --frozen --no-dev

# Place executables in the environment at the front of the path.
ENV PATH="/app/.venv/bin:$PATH"

CMD ["a3md"]
