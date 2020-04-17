# -*- coding: utf-8 -*-
"""Archivematica MCPServer API."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
from concurrent import futures

from django.conf import settings
from google.rpc import code_pb2
from grpc import server
from grpc_reflection.v1alpha import reflection

from a3m.main.models import Transfer
from a3m.server.db import auto_close_old_connections
from a3m.server.packages import create_package
from a3m.server.rpc import a3m_pb2
from a3m.server.rpc import a3m_pb2_grpc


logger = logging.getLogger("archivematica.mcp.server.rpc_server")


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
            logger.warning("Submission error: %s", err)
            context.abort(code_pb2.INTERNAL, "Submission error")
        return a3m_pb2.SubmitReply(id=str(transfer.pk))

    @auto_close_old_connections()
    def Status(self, request, context):
        try:
            Transfer.objects.get(pk=request.id)
        except Transfer.DoesNotExist:
            context.abort(code_pb2.NOT_FOUND, "Transfer not found")
        except Exception as err:
            logger.warning("Error loading transfer: %s", err)
            context.abort(code_pb2.INTERNAL, "Unhandled error")

        active = self.package_queue.is_package_active(request.id)
        if active:
            return a3m_pb2.StatusReply(status=a3m_pb2.PROCESSING)

        # FAILED, REJECTED, COMPLETE, PROCESSING, AWAITING_DECISION
        status = a3m_pb2.COMPLETE

        # TODO: do what's in https://git.io/JfvX4
        # TODO: deal with transition from Transfer to SIP

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
