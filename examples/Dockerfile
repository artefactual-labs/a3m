FROM ghcr.io/artefactual-labs/a3m:main

COPY webapp.py /a3m

USER root

RUN set -ex \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends libnss3-tools \
	&& rm -rf /var/lib/apt/lists/* \
	&& curl -Ls "https://github.com/FiloSottile/mkcert/releases/download/v1.4.1/mkcert-v1.4.1-linux-amd64" > /usr/bin/mkcert \
	&& chmod +x /usr/bin/mkcert \
	&& mkcert -install \
	&& mkcert example.com "*.example.com" example.test localhost 127.0.0.1 ::1

USER a3m

ENTRYPOINT ["python", "webapp.py"]
