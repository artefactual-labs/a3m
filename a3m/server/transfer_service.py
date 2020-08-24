import logging

from google.rpc import code_pb2

from a3m.main.models import Task
from a3m.server.packages import get_package_status
from a3m.server.packages import Package
from a3m.server.packages import PackageNotFoundError
from a3m.server.rpc.proto import a3m_pb2
from a3m.server.rpc.proto import a3m_pb2_grpc

logger = logging.getLogger(__name__)


class TransferService(a3m_pb2_grpc.TransferServicer):
    def __init__(self, workflow, package_queue, executor):
        self.workflow = workflow
        self.package_queue = package_queue
        self.executor = executor

    def Submit(self, request, context):
        try:
            package = Package.create_package(
                self.package_queue,
                self.executor,
                self.workflow,
                request.name,
                request.url,
            )
        except Exception as err:
            logger.warning("TransferService.Submit handler error: %s", err)
            context.abort(code_pb2.INTERNAL, "Unknown error")
        return a3m_pb2.SubmitReply(id=str(package.uuid))

    def Read(self, request, context):
        try:
            package_status = get_package_status(self.package_queue, request.id)
        except PackageNotFoundError:
            context.abort(code_pb2.NOT_FOUND, "Package not found")
        except Exception as err:
            logger.warning("TransferService.Status handler error: %s", err)
            context.abort(code_pb2.INTERNAL, "Unknown error")
        reply = a3m_pb2.ReadReply(status=package_status.status)
        if package_status.job:
            reply.job = package_status.job
        if package_status.jobs:
            reply.jobs.extend(package_status.jobs)
        return reply

    def ListTasks(self, request, context):
        if not request.job_id:
            context.abort(code_pb2.INVALID_ARGUMENT, "job_id is mandatory")
        reply = a3m_pb2.ListTasksReply()
        for item in Task.objects.filter(job_id=request.job_id):
            reply.tasks.append(
                a3m_pb2.Task(
                    id=item.pk,
                    file_id=item.fileuuid,
                    exit_code=item.exitcode,
                    filename=item.filename,
                    execution=item.execution,
                    arguments=item.arguments,
                    stdout=item.stdout,
                    stderr=item.stderror,
                )
            )
        return reply
