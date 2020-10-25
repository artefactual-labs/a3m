from contextlib import ContextDecorator

import grpc
from django.conf import settings

from a3m.server.rpc import Client


class ClientWrapper(ContextDecorator):
    """A context manager that provides a a3m client or client-server instance.

    Use ``address`` to indicate the location of the a3m server. When undefined,
    this wrapper launches an embedded server and sets up the client accordingly.
    Used resources are automatically cleaned up.
    """

    BIND_LOCAL_ADDRESS = "localhost:0"

    def __init__(self, address=None, wait_for_ready=False):
        self.address = address
        self.wait_for_ready = wait_for_ready

        self._create_server()
        self._create_client()

    def __enter__(self):
        if self.server is not None:
            self.server.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.server is not None:
            self.server.stop()
        if exc_type:
            return False

    def _create_server(self):
        self.server = None

        if self.address is not None:
            return

        from a3m.server.runner import create_server

        server_credentials = grpc.local_server_credentials(
            grpc.LocalConnectionType.LOCAL_TCP
        )
        self.server = create_server(
            self.BIND_LOCAL_ADDRESS,
            server_credentials,
            settings.CONCURRENT_PACKAGES,
            settings.BATCH_SIZE,
            settings.WORKER_THREADS,
            settings.RPC_THREADS,
            settings.DEBUG,
        )

        # Compute address since port was dynamically assigned.
        self.address = f"localhost:{self.server.grpc_port}"

    def _create_client(self):
        channel = grpc.insecure_channel(self.address)
        self.client = Client(channel, wait_for_ready=self.wait_for_ready)
