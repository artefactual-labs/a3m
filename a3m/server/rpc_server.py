"""Archivematica MCPServer API."""
import logging
from concurrent import futures

from django.conf import settings
from google.rpc import code_pb2
from grpc import server
from grpc_reflection.v1alpha import reflection

from a3m.server.packages import create_package
from a3m.server.packages import get_package_status
from a3m.server.packages import PackageNotFoundError
from a3m.server.rpc import a3m_pb2
from a3m.server.rpc import a3m_pb2_grpc


logger = logging.getLogger(__name__)


class TransferService(a3m_pb2_grpc.TransferServicer):
    def __init__(self, workflow, package_queue, executor):
        self.workflow = workflow
        self.package_queue = package_queue
        self.executor = executor

    def Submit(self, request, context):
        try:
            transfer = create_package(
                self.package_queue,
                self.executor,
                self.workflow,
                request.name,
                request.url,
            )
        except Exception as err:
            logger.warning("Submit handler error: %s", err)
            context.abort(code_pb2.INTERNAL, "Unknown error")
        return a3m_pb2.SubmitReply(id=str(transfer.pk))

    def Status(self, request, context):
        try:
            status, _ = get_package_status(request.id)
        except PackageNotFoundError:
            context.abort(code_pb2.NOT_FOUND, "Package not found")
        except Exception as err:
            logger.warning("Status handler error: %s", err)
            context.abort(code_pb2.INTERNAL, "Unknown error")
        return a3m_pb2.StatusReply(status=status)


def start(workflow, shutdown_event, package_queue, executor):
    transfer_service = TransferService(workflow, package_queue, executor)
    grpc_server = server(futures.ThreadPoolExecutor(max_workers=settings.RPC_THREADS))
    a3m_pb2_grpc.add_TransferServicer_to_server(transfer_service, grpc_server)
    SERVICE_NAMES = (
        a3m_pb2.DESCRIPTOR.services_by_name["Transfer"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, grpc_server)
    grpc_server.add_insecure_port(settings.RPC_BIND_ADDRESS)

    grpc_server.start()

    shutdown_event.wait()
    grpc_server.stop(None)
