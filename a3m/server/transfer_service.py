import logging

from google.protobuf import timestamp_pb2
from google.rpc import code_pb2

from a3m.api.transferservice import v1beta1 as transfer_service_api
from a3m.main.models import Task
from a3m.server import shared_dirs
from a3m.server.packages import get_package_status
from a3m.server.packages import Package
from a3m.server.packages import PackageNotFoundError

logger = logging.getLogger(__name__)


class TransferService(transfer_service_api.service_pb2_grpc.TransferServiceServicer):
    def __init__(self, workflow, package_queue, executor):
        self.workflow = workflow
        self.package_queue = package_queue
        self.executor = executor

    def Submit(self, request, context):
        config = request.config if request.HasField("config") else None
        try:
            package = Package.create_package(
                self.package_queue,
                self.executor,
                self.workflow,
                request.name,
                request.url,
                config,
            )
        except Exception as err:
            logger.warning("TransferService.Submit handler error: %s", err)
            context.abort(code_pb2.INTERNAL, "Unknown error")
        return transfer_service_api.request_response_pb2.SubmitResponse(
            id=str(package.uuid)
        )

    def Read(self, request, context):
        try:
            package_status = get_package_status(self.package_queue, request.id)
        except PackageNotFoundError:
            context.abort(code_pb2.NOT_FOUND, "Package not found")
        except Exception as err:
            logger.warning("TransferService.Status handler error: %s", err)
            context.abort(code_pb2.INTERNAL, "Unknown error")
        resp = transfer_service_api.request_response_pb2.ReadResponse(
            status=package_status.status
        )
        if package_status.job:
            resp.job = package_status.job
        if package_status.jobs:
            resp.jobs.extend(package_status.jobs)
        return resp

    def ListTasks(self, request, context):
        if not request.job_id:
            context.abort(code_pb2.INVALID_ARGUMENT, "job_id is mandatory")
        resp = transfer_service_api.request_response_pb2.ListTasksResponse()
        for item in Task.objects.filter(job_id=request.job_id):
            start_time = timestamp_pb2.Timestamp()
            start_time.FromDatetime(item.starttime)
            end_time = timestamp_pb2.Timestamp()
            end_time.FromDatetime(item.endtime)
            resp.tasks.append(
                transfer_service_api.request_response_pb2.Task(
                    id=item.pk,
                    file_id=item.fileuuid,
                    exit_code=item.exitcode,
                    filename=item.filename,
                    execution=item.execution,
                    arguments=item.arguments,
                    stdout=item.stdout,
                    stderr=item.stderror,
                    start_time=start_time,
                    end_time=end_time,
                )
            )
        return resp

    def Empty(self, request, context):
        # TODO: Add check: files should not be deleted if a3m is currently processing.
        resp = transfer_service_api.request_response_pb2.EmptyResponse()
        shared_dirs.empty()
        shared_dirs.create()
        return resp
