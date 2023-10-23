"""
Start and run MCPServer.

`main` goes through the following steps:
1. A `ThreadPoolExecutor` is initialized with a configurable number of threads
(default ncpus).
2. A signal listener is setup to handle shutdown on SIGINT/SIGTERM events.
3. The default workflow is loaded (from workflow.json).
4. The configured SHARED_DIRECTORY is populated with the expected directory
structure, and default processing configs added.
5. Any in progress Job and Task entries in the database are marked as errors,
as they are presumed to have been the result of a shutdown while processing.
6. If Prometheus metrics are enabled, an thread is started to serve metrics for
scraping.
7. A `PackageQueue` (see the `queues` module) is initialized.
8. A configured number (default 4) of RPCServer (see the `rpc_server` module)
threads are started to handle gearman "RPC" requests from the dashboard.
9. A watched directory thread is started to observe changes in any of the
watched dirs as set in the workflow.
10. The `PackageQueue.work` processing loop is started on the main thread.
"""
import concurrent.futures
import enum
import logging
import threading

import grpc
from django.conf import settings as premis_settings
from grpc_reflection.v1alpha import reflection

from a3m import __version__
from a3m.api.transferservice import v1beta1 as transfer_service_api
from a3m.main import models
from a3m.server import metrics
from a3m.server import shared_dirs
from a3m.server.db import migrate
from a3m.server.jobs import Job
from a3m.server.queues import PackageQueue
from a3m.server.tasks import Task
from a3m.server.tasks.backends import get_task_backend
from a3m.server.tasks.backends import TaskBackend
from a3m.server.transfer_service import TransferService
from a3m.server.workflow import load_default_workflow
from a3m.server.workflow import Workflow

logger = logging.getLogger(__name__)


@enum.unique
class ServerStage(enum.Enum):
    STOPPED = "stopped"
    STARTED = "started"
    GRACE = "grace"


class Server:
    """a3m server.

    It runs the gRPC API server and the workflow engine, using independent pools
    of threads. It accepts a :class:`a3m.server.workflow.Workflow` which can be
    customized as needed.
    """

    def __init__(
        self,
        bind_address: str,
        server_credentials: grpc.ServerCredentials | None,
        workflow: Workflow,
        max_concurrent_packages: int,
        batch_size: int,
        queue_executor: concurrent.futures.ThreadPoolExecutor,
        grpc_executor: concurrent.futures.ThreadPoolExecutor,
        debug: bool = False,
    ):
        self.stage = ServerStage.STOPPED
        self.lock = threading.RLock()
        self.termination_event = threading.Event()

        # A3M-TODO: inject task backend via PackageQueue.
        TaskBackend.TASK_BATCH_SIZE = batch_size

        self.workflow = workflow
        self.queue_executor = queue_executor
        self.queue_shutdown_event = threading.Event()
        self.queue = PackageQueue(
            self.queue_executor,
            self.queue_shutdown_event,
            max_concurrent_packages=max_concurrent_packages,
            debug=debug,
        )
        self.grpc_executor = grpc_executor
        self.grpc_server = grpc.server(grpc_executor)
        self.grpc_port = self.grpc_server.add_insecure_port(bind_address)

        self._mount_services()

    def _mount_services(self):
        transfer_service = TransferService(
            self.workflow, self.queue, self.queue_executor
        )
        transfer_service_api.service_pb2_grpc.add_TransferServiceServicer_to_server(
            transfer_service, self.grpc_server
        )

        services = tuple(
            service.full_name
            for service in transfer_service_api.service_pb2.DESCRIPTOR.services_by_name.values()
        ) + (reflection.SERVICE_NAME,)
        reflection.enable_server_reflection(services, self.grpc_server)

    def start(self):
        """Starts this Server.

        This method may only be called once. (i.e. it is not idempotent).
        """
        with self.lock:
            if self.stage is not ServerStage.STOPPED:
                raise ValueError("Cannot start already-started server!")

            self.stage = ServerStage.STARTED

            threading.Thread(target=self.queue.work).start()
            threading.Thread(target=self.grpc_server.start).start()

    def wait_for_termination(self, timeout=None):
        """Blocks current thread until the server stops."""
        while not self.termination_event.is_set():
            self.termination_event.wait(timeout=None)
        return False

    def stop(self, grace=None):
        """Stops this Server."""
        with self.lock:
            shutdown_event = threading.Event()

            if self.stage is ServerStage.STOPPED:
                shutdown_event.set()
                return shutdown_event

            self.stage = ServerStage.GRACE

            def _stop():
                logger.info("Shutting down...")

                self.grpc_server.stop(grace)
                self.queue_shutdown_event.set()
                self.queue.wait_for_termination()
                get_task_backend().shutdown(wait=False)

                shutdown_event.set()
                self.termination_event.set()
                self.stage = ServerStage.STOPPED

            threading.Thread(target=_stop).start()

            shutdown_event.wait()
            return shutdown_event


def create_server(
    bind_address,
    server_credentials,
    max_concurrent_packages,
    batch_size,
    queue_workers,
    grpc_workers,
    debug=False,
):
    """Create a3m server ready to use.

    It bootstraps some bits locally needed, like the database, the local
    processing directory or the pool of threads. It wraps
    :class:`a3m.server.runner.Server`.
    """
    workflow = load_default_workflow()

    shared_dirs.create()

    migrate()
    update_agents()

    Job.cleanup_old_db_entries()
    Task.cleanup_old_db_entries()

    metrics.init_labels(workflow)
    metrics.start_prometheus_server()

    return Server(
        bind_address,
        server_credentials,
        workflow,
        max_concurrent_packages,
        batch_size,
        concurrent.futures.ThreadPoolExecutor(max_workers=queue_workers),
        concurrent.futures.ThreadPoolExecutor(max_workers=grpc_workers),
        debug,
    )


def update_agents():
    """Create or update software and organization agents."""

    models.Agent.objects.update_or_create(
        agenttype="software",
        name="a3m",
        identifiertype="preservation system",
        defaults={
            "identifiervalue": f"a3m version={__version__}",
        },
    )

    if premis_settings.ORG_ID and premis_settings.ORG_NAME:
        models.Agent.objects.update_or_create(
            agenttype="organization",
            identifiertype="repository code",
            defaults={
                "identifiervalue": premis_settings.ORG_ID,
                "name": premis_settings.ORG_NAME,
            },
        )
