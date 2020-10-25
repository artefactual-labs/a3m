import logging
from typing import Callable
from typing import Optional

import tenacity
from grpc import Channel
from grpc import RpcError

from a3m import __version__
from a3m.server.rpc.proto import a3m_pb2
from a3m.server.rpc.proto import a3m_pb2_grpc


logger = logging.getLogger(__name__)


# Default duration in seconds of RPC calls.
_GRPC_DEFAULT_TIMEOUT_SECS = 30

# Metadata key containing the client version.
_VERSION_METADATA_KEY = "version"


class Client:
    """a3m gRPC API client."""

    def __init__(
        self,
        channel: Channel,
        rpc_timeout: Optional[int] = _GRPC_DEFAULT_TIMEOUT_SECS,
        wait_for_ready: bool = False,
    ):
        self.transfer_stub = a3m_pb2_grpc.TransferStub(channel)
        self.rpc_timeout = rpc_timeout
        self.wait_for_ready = wait_for_ready

    def _unary_call(self, api_method, request):
        rpc_name = request.__class__.__name__.replace("Request", "")
        logger.debug("RPC call %s with request: %r", rpc_name, request)
        try:
            return api_method(
                request,
                timeout=self.rpc_timeout,
                metadata=Client.version_metadata(),
                wait_for_ready=self.wait_for_ready,
            )
        except RpcError as e:
            logger.warning("RPC call %s got error %s", rpc_name, e)
            raise

    @staticmethod
    def version_metadata():
        return ((_VERSION_METADATA_KEY, __version__),)

    def submit(self, url: str, name: str, config: a3m_pb2.ProcessingConfig = None):
        request = a3m_pb2.SubmitRequest(name=name, url=url, config=config)
        return self._unary_call(self.transfer_stub.Submit, request)

    def read(self, package_id: str):
        request = a3m_pb2.ReadRequest(id=package_id)
        return self._unary_call(self.transfer_stub.Read, request)

    def wait_until_complete(self, package_id: str, spin_cb: Callable = None):
        """Blocks until processing of a package has completed."""

        def _should_continue(resp):
            if resp.status == a3m_pb2.PROCESSING:
                return True
            return False

        def _callback(retry_state):
            if spin_cb is not None:
                spin_cb(retry_state)

        @tenacity.retry(
            wait=tenacity.wait_fixed(1),
            retry=tenacity.retry(tenacity.retry_if_result(_should_continue)),
            after=_callback,
        )
        def _poll():
            """Retries while the package is processing."""
            return self.read(package_id)

        return _poll()

    def list_tasks(self, job_id: str):
        request = a3m_pb2.ListTasksRequest(job_id=job_id)
        return self._unary_call(self.transfer_stub.ListTasks, request)
