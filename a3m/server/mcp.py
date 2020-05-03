"""
Start and run MCPServer via the `main` function.

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
import logging
import os
import signal
import threading
from platform import python_version

import django

django.setup()
from django.conf import settings

from a3m.server import metrics
from a3m.server import rpc_server
from a3m.server import shared_dirs
from a3m.server.db import migrate
from a3m.server.jobs import Job
from a3m.server.queues import PackageQueue
from a3m.server.tasks import Task
from a3m.server.tasks.backends import get_task_backend
from a3m.server.workflow import load_default_workflow


logger = logging.getLogger(__name__)


def main(shutdown_event=None):
    logger.info(
        f"Starting a3m... (pid={os.getpid()} uid={os.getuid()} python={python_version()})"
    )

    # Tracks whether a sigterm has been received or not
    if shutdown_event is None:
        shutdown_event = threading.Event()
    executor = concurrent.futures.ThreadPoolExecutor(
        # Lower than the default, since we typically run many processes per system.
        # Defaults to the number of cores available, which is twice as many as the
        # default concurrent packages limit.
        max_workers=settings.WORKER_THREADS
    )

    def signal_handler(signo, frame):
        """Used to handle the stop/kill command signals (SIGINT, SIGKILL)"""
        logger.info("Received termination signal (%s)", signal.Signals(signo).name)

        shutdown_event.set()
        executor.shutdown(wait=False)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    workflow = load_default_workflow()
    logger.debug("Loaded workflow.")

    shared_dirs.create()

    logger.info("Preparing database...")
    migrate()
    Job.cleanup_old_db_entries()
    Task.cleanup_old_db_entries()

    metrics.init_labels(workflow)
    metrics.start_prometheus_server()

    package_queue = PackageQueue(executor, shutdown_event, debug=settings.DEBUG)

    rpc_thread = threading.Thread(
        target=rpc_server.start,
        args=(workflow, shutdown_event, package_queue, executor),
        name="gRPC server",
    )
    rpc_thread.start()
    logger.info("Started gRPC server (%s)", settings.RPC_BIND_ADDRESS)

    # Blocks until shutdown_event is set by signal_handler
    package_queue.work()

    # We got a shutdown signal, so cleanup threads
    rpc_thread.join(0.1)
    logger.debug("gRPC server stopped.")

    # Shut down task backend.
    get_task_backend().shutdown(wait=False)

    logger.info("a3m shutdown complete.")


if __name__ == "__main__":
    main()
