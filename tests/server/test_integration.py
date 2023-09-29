import concurrent.futures
import os
import threading
import uuid

import pytest
from django.utils import timezone

from a3m.api.transferservice.v1beta1.request_response_pb2 import ProcessingConfig
from a3m.main import models
from a3m.server.jobs import DirectoryClientScriptJob
from a3m.server.jobs import FilesClientScriptJob
from a3m.server.jobs import JobChain
from a3m.server.jobs import NextLinkDecisionJob
from a3m.server.packages import Package
from a3m.server.queues import PackageQueue
from a3m.server.tasks import TaskBackend
from a3m.server.workflow import load as load_workflow


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
INTEGRATION_TEST_PATH = os.path.join(FIXTURES_DIR, "workflow-integration-test.json")


class EchoBackend(TaskBackend):
    def __init__(self):
        self.tasks = {}

    def submit_task(self, job, task):
        if job.uuid not in self.tasks:
            self.tasks[job.uuid] = []
        self.tasks[job.uuid].append(task)

    def wait_for_results(self, job):
        for task in self.tasks[job.uuid]:
            task.exit_code = 0
            task.stdout = task.arguments
            task.stderr = task.arguments
            task.finished_timestamp = timezone.now()

            yield task


@pytest.fixture
def workflow(request):
    with open(INTEGRATION_TEST_PATH) as workflow_file:
        return load_workflow(workflow_file)


@pytest.fixture
def package_queue(request):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    return PackageQueue(executor, threading.Event(), debug=True)


class FakeUnit:
    def __init__(self, pk):
        self.pk = pk


@pytest.fixture
def package(request):
    return Package(
        "package-1",
        "file:///tmp/foobar-1.gz",
        ProcessingConfig(),
        models.Transfer.objects.create(pk=uuid.uuid4()),
        models.SIP.objects.create(pk=uuid.uuid4()),
    )


@pytest.fixture
def dummy_file_replacements(request):
    files = []
    for x in range(3):
        files.append(
            {
                r"%relativeLocation%": f"transfer_path/file{x}",
                r"%fileUUID%": str(uuid.uuid4()),
            }
        )

    return files


@pytest.mark.django_db(transaction=True)
def test_workflow_integration(
    mocker,
    settings,
    tmp_path,
    workflow,
    package_queue,
    package,
    dummy_file_replacements,
):
    # Setup our many mocks
    echo_backend = EchoBackend()
    settings.SHARED_DIRECTORY = str(tmp_path)
    settings.PROCESSING_DIRECTORY = str(tmp_path / "processing")
    mocker.patch.dict(
        "a3m.server.packages.BASE_REPLACEMENTS",
        {r"%processingDirectory%": settings.PROCESSING_DIRECTORY},
    )

    mock_get_task_backend = mocker.patch(
        "a3m.server.jobs.client.get_task_backend", return_value=echo_backend
    )
    mocker.patch.object(package, "files", return_value=dummy_file_replacements)

    # Schedule the first job
    initiator_link = workflow.get_initiator()
    first_job_chain = JobChain(package, workflow, initiator_link)
    job = next(first_job_chain)
    package_queue.schedule_job(job)

    assert package_queue.job_queue.qsize() == 1
    assert len(package_queue.active_packages) == 1
    assert package.uuid in package_queue.active_packages

    # Process the first job (DirectoryClientScriptJob)
    future = package_queue.process_one_job(timeout=1.0)
    concurrent.futures.wait([future], timeout=1.0)

    mock_get_task_backend.assert_called_once()
    task = echo_backend.tasks[job.uuid][0]

    assert isinstance(job, DirectoryClientScriptJob)
    assert job.exit_code == 0
    assert task.arguments == '"{}" "{}"'.format(
        settings.PROCESSING_DIRECTORY, package.subid
    )

    # Next job in chain should be queued
    assert package_queue.job_queue.qsize() == 1
    job = future.result()

    # Process the second job (FilesClientScriptJob)
    future = package_queue.process_one_job(timeout=1.0)
    concurrent.futures.wait([future], timeout=1.0)

    tasks = echo_backend.tasks[job.uuid]

    assert isinstance(job, FilesClientScriptJob)
    assert job.exit_code == 0
    assert len(tasks) == len(dummy_file_replacements)
    for task, replacement in zip(tasks, dummy_file_replacements):
        assert task.arguments == '"{}"'.format(replacement[r"%fileUUID%"])

    # Next job in chain should be queued
    assert package_queue.job_queue.qsize() == 1
    job = future.result()

    # Process the third job (DirectoryClientScriptJob)
    future = package_queue.process_one_job(timeout=1.0)
    concurrent.futures.wait([future], timeout=1.0)

    assert isinstance(job, DirectoryClientScriptJob)
    assert job.exit_code == 0

    # Next job in chain should be queued
    assert package_queue.job_queue.qsize() == 1
    job = future.result()

    # Process the fourth job (DirectoryClientScriptJob)
    future = package_queue.process_one_job(timeout=1.0)
    concurrent.futures.wait([future], timeout=1.0)

    assert isinstance(job, DirectoryClientScriptJob)
    assert job.exit_code == 0

    # Next job in chain should be queued
    assert package_queue.job_queue.qsize() == 1
    job = future.result()

    # Process the fifth job (NextLinkDecisionJob)
    future = package_queue.process_one_job(timeout=1.0)
    concurrent.futures.wait([future], timeout=1.0)

    assert isinstance(job, NextLinkDecisionJob)
    assert job.exit_code == 0

    # Next job in chain should be queued
    assert package_queue.job_queue.qsize() == 1
    job = future.result()

    # Process the sixth job (UpdateContextDecisionJob)
    future = package_queue.process_one_job(timeout=1.0)
    concurrent.futures.wait([future], timeout=1.0)

    # Out job chain should have been redirected to the final link
    assert job.job_chain.current_link.id == "f8e4c1ee-3e43-4caa-a664-f6b6bd8f156e"
    assert package_queue.job_queue.qsize() == 1
    job = future.result()

    assert isinstance(job, DirectoryClientScriptJob)
    assert job.exit_code is None

    # Process the last job (DirectoryClientScriptJob)
    future = package_queue.process_one_job(timeout=1.0)
    concurrent.futures.wait([future], timeout=1.0)

    assert job.exit_code == 0

    # Workflow is over; we're done
    assert package_queue.job_queue.qsize() == 0
