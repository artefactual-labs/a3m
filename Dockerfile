# syntax=docker/dockerfile:1.10.0-labs

ARG SYSTEM_IMAGE=default-system
ARG UV_IMAGE=default-uv
ARG USER_ID=1000
ARG GROUP_ID=1000

# Keep the default image references literal for Dependabot. The image
# arguments can still override the corresponding stages.

#
# Base
#

FROM ubuntu:22.04 AS default-system
FROM ${SYSTEM_IMAGE} AS base

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN set -ex \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
	apt-transport-https \
	ca-certificates \
	curl \
	git \
	gnupg \
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
	&& mkdir -p /etc/apt/keyrings \
	&& curl --retry 3 -fsSL https://packages.archivematica.org/GPG-KEY-archivematica | gpg --dearmor -o /etc/apt/keyrings/archivematica.gpg \
	&& echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/archivematica.gpg] https://packages.archivematica.org/1.19.x/ubuntu-externals jammy main" > /etc/apt/sources.list.d/archivematica.list \
	&& add-apt-repository --no-update --yes "deb http://archive.ubuntu.com/ubuntu/ jammy multiverse" \
	&& add-apt-repository --no-update --yes "deb http://archive.ubuntu.com/ubuntu/ jammy-security universe" \
	&& add-apt-repository --no-update --yes "deb http://archive.ubuntu.com/ubuntu/ jammy-updates multiverse" \
	&& curl --retry 3 -fsSL -o /tmp/repo-mediaarea_1.0-25_all.deb https://mediaarea.net/repo/deb/repo-mediaarea_1.0-25_all.deb \
	&& dpkg -i /tmp/repo-mediaarea_1.0-25_all.deb \
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
	jhove=1.34.0-1~22.04 \
	libimage-exiftool-perl \
	libevent-dev \
	libjansson4 \
	mediainfo \
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

FROM ghcr.io/astral-sh/uv:0.13.6@sha256:af22a52f5eafef3d78e551599d405c02df61919d18028f0cea8eda93bc9986d0 AS default-uv
FROM ${UV_IMAGE} AS uv

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

# Keep the interpreter managed by uv, independently of the base image.
ENV UV_PYTHON_PREFERENCE=only-managed

# Change the current user.
USER a3m

# Install the project into `/app`.
WORKDIR /app

# Install the project's dependencies and remove pip from the managed Python.
# uv handles installs; removing pip here avoids shipping its vendored packages.
# Cache the Python archive across dependency-layer rebuilds.
RUN --mount=type=cache,target=/home/a3m/.cache/uv,uid=${USER_ID},gid=${GROUP_ID} \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=.python-version,target=.python-version \
    UV_PYTHON_CACHE_DIR=/home/a3m/.cache/uv/python uv sync --locked --no-install-project --no-dev \
    && A3M_BASE_PREFIX=$(.venv/bin/python -c 'import sys; print(sys.base_prefix)') \
    && uv pip uninstall --python "${A3M_BASE_PREFIX}/bin/python3" --break-system-packages pip \
    && rm -f "${A3M_BASE_PREFIX}"/lib/python3.*/ensurepip/_bundled/pip-*.whl

# Add the rest of the project source code and install it.
# Installing separately from its dependencies allows optimal layer caching.
COPY --exclude=.git . /app
RUN --mount=type=cache,target=/home/a3m/.cache/uv,uid=${USER_ID},gid=${GROUP_ID} \
	--mount=type=bind,source=.git,target=.git \
    uv sync --locked --no-dev

# Place executables in the environment at the front of the path.
ENV PATH="/app/.venv/bin:$PATH"

CMD ["a3md"]
