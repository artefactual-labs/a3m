from concurrent.futures import ThreadPoolExecutor
from datetime import timezone
from uuid import uuid4

import grpc
import pytest
from django.utils import timezone as django_timezone
from grpc_reflection.v1alpha import reflection_pb2
from grpc_reflection.v1alpha import reflection_pb2_grpc

from a3m.api.transferservice import v1beta1 as transfer_service_api
from a3m.main import models
from a3m.server.packages import Package
from a3m.server.rpc import Client
from a3m.server.runner import Server
from a3m.server.tasks import TaskBackend
from a3m.server.workflow import load_default_workflow


@pytest.fixture
def rpc_server(monkeypatch):
    monkeypatch.setattr(TaskBackend, "TASK_BATCH_SIZE", TaskBackend.TASK_BATCH_SIZE)
    with ThreadPoolExecutor(max_workers=1) as queue_executor:
        with ThreadPoolExecutor(max_workers=1) as grpc_executor:
            server = Server(
                "localhost:0",
                None,
                load_default_workflow(),
                1,
                1,
                queue_executor,
                grpc_executor,
            )
            # Exercise the mounted production RPC services without starting
            # preservation workers: this test controls the package lifecycle.
            server.grpc_server.start()
            try:
                with grpc.insecure_channel(f"localhost:{server.grpc_port}") as channel:
                    grpc.channel_ready_future(channel).result(timeout=5)
                    yield server, channel
            finally:
                server.grpc_server.stop(0).wait(timeout=5)


@pytest.mark.django_db(transaction=True)
def test_rpc_reflection_polling_and_preservation_task_serialization(rpc_server):
    server, channel = rpc_server
    client = Client(channel, rpc_timeout=5)
    messages = transfer_service_api.request_response_pb2
    service_name = "a3m.api.transferservice.v1beta1.TransferService"
    reflection = reflection_pb2_grpc.ServerReflectionStub(channel)
    responses = list(
        reflection.ServerReflectionInfo(
            iter(
                [
                    reflection_pb2.ServerReflectionRequest(
                        file_containing_symbol=service_name
                    )
                ]
            ),
            timeout=5,
        )
    )
    assert responses[0].file_descriptor_response.file_descriptor_proto

    transfer = models.Transfer.objects.create(uuid=str(uuid4()))
    sip = models.SIP.objects.create(uuid=str(uuid4()))
    package = Package("preservation", "file:///example.txt", None, transfer, sip)
    server.queue.active_packages[sip.uuid] = package
    now = django_timezone.now()
    job = models.Job.objects.create(
        jobuuid=uuid4(),
        createdtime=now,
        sipuuid=sip.uuid,
        jobtype="a3m - Store AIP",
        microservicegroup="Store AIP",
        currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
    )
    task = models.Task.objects.create(
        taskuuid=str(uuid4()),
        job=job,
        createdtime=now,
        starttime=now,
        endtime=now,
        fileuuid=str(uuid4()),
        filename="objects/℃.txt",
        stdout="Preserved ℃.txt",
        exitcode=0,
    )
    observed_statuses = []

    def complete_package(retry_state):
        observed_statuses.append(retry_state.outcome.result().status)
        server.queue.active_packages.pop(sip.uuid)

    response = client.wait_until_complete(sip.uuid, spin_cb=complete_package)

    assert observed_statuses == [messages.PACKAGE_STATUS_PROCESSING]
    assert response.status == messages.PACKAGE_STATUS_COMPLETE
    assert response.job == "Store AIP"
    assert len(response.jobs) == 1
    assert response.jobs[0].id == str(job.pk)
    assert (
        response.jobs[0].start_time.ToDatetime(tzinfo=timezone.utc) == job.createdtime
    )
    tasks = client.list_tasks(str(job.pk)).tasks
    assert len(tasks) == 1
    assert tasks[0].id == task.pk
    assert tasks[0].filename == task.filename
    assert tasks[0].stdout == task.stdout
    assert tasks[0].exit_code == 0
    assert tasks[0].start_time.ToDatetime(tzinfo=timezone.utc) == now
    assert tasks[0].end_time.ToDatetime(tzinfo=timezone.utc) == now
