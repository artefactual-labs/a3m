import logging
import os
import platform
import signal

import grpc
from django.conf import settings

from a3m import __version__
from a3m.cli.common import configure_xml_catalog_files
from a3m.cli.common import init_django
from a3m.cli.common import suppress_warnings


logger = logging.getLogger(__name__)


def main():
    init_django()
    suppress_warnings()
    configure_xml_catalog_files()

    from a3m.server.runner import create_server

    logger.info(
        f"Starting a3m... (version={__version__} pid={os.getpid()} "
        f"uid={os.getuid()} python={platform.python_version()} "
        f"listen={settings.RPC_BIND_ADDRESS})"
    )

    # A3M-TODO: make this configurable, e.g. local tcp, local uds, tls certs...
    # (see https://grpc.github.io/grpc/python/grpc.html#create-server-credentials for more)
    server_credentials = grpc.local_server_credentials(
        grpc.LocalConnectionType.LOCAL_TCP
    )

    server = create_server(
        settings.RPC_BIND_ADDRESS,
        server_credentials,
        settings.CONCURRENT_PACKAGES,
        settings.BATCH_SIZE,
        settings.WORKER_THREADS,
        settings.RPC_THREADS,
        settings.DEBUG,
    )
    server.start()

    def signal_handler(signo, frame):
        logger.info("Received termination signal (%s)", signal.Signals(signo).name)
        server.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    server.wait_for_termination()

    logger.info("a3m shutdown complete.")


if __name__ == "__main__":
    main()
