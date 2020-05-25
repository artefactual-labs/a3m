"""Integration with Enduro.

This module implements an activity worker for Enduro where Cadence acts as the
service broker dispatching tasks while Enduro orchestrates the workflow. This
model is similar to Archivematica (MCPServer ⇋ Gearman ⇋ MCPClient) where this
module implements the worker.

It is based on the ``workflow_service_activity_worker`` example found in
``cadence-python``.
"""
import json
import logging
import threading
import time
from concurrent import futures

from cadence.cadence_types import PollForActivityTaskRequest
from cadence.cadence_types import PollForActivityTaskResponse
from cadence.cadence_types import RecordActivityTaskHeartbeatRequest
from cadence.cadence_types import RespondActivityTaskCompletedRequest
from cadence.cadence_types import RespondActivityTaskFailedRequest
from cadence.cadence_types import TaskList
from cadence.cadence_types import TaskListMetadata
from cadence.constants import DEFAULT_SOCKET_TIMEOUT_SECONDS
from cadence.worker import StopRequestedException
from cadence.workflowservice import WorkflowService
from tenacity import before_sleep_log
from tenacity import retry
from tenacity import retry_unless_exception_type
from tenacity import wait_exponential

from a3m.server.packages import get_package_status
from a3m.server.packages import Package
from a3m.server.rpc import a3m_pb2


logger = logging.getLogger(__name__)


class PollError(Exception):
    """Activity worker poller error."""


class UnretryableError(Exception):
    """Activity worker unretryable error."""


class ActivityError(Exception):
    """Business-level function error."""


class ActivityWorker:
    """Enduro worker.

    It receives activity tasks delivered by Enduro by subscribing to an activity
    task list. Once the task is received, it invokes the corresponding activity.
    """

    def __init__(
        self,
        address,
        domain,
        task_list,
        shutdown_event,
        package_queue,
        executor,
        workflow,
    ):
        self.host, self.port = self._parse_address(address)
        self.domain = domain
        self.task_list = task_list
        self.package_queue = package_queue
        self.executor = executor
        self.workflow = workflow

        if shutdown_event is None:
            shutdown_event = threading.Event()
        self.shutdown_event = shutdown_event

    def start(self):
        """It starts the worker loop and returns."""
        self.future = self.executor.submit(self._work)
        self.future.add_done_callback(self._work_done_callback)

    def _parse_address(self, address):
        host, sep, port = address.partition(":")
        if not sep:
            raise ValueError("Server address is empty or incorrect")
        return host, int(port)

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_unless_exception_type(UnretryableError),
        before_sleep=before_sleep_log(logger, logging.WARNING, exc_info=False),
    )
    def _work(self):
        """Worker loop."""
        if self.shutdown_event.is_set():
            raise UnretryableError("Worker is shutting down")

        self.service = WorkflowService.create(
            self.host, self.port, timeout=DEFAULT_SOCKET_TIMEOUT_SECONDS
        )
        self.service.connection.set_next_timeout_cb(self._conn_timeout_callback)
        logger.info(
            "ActivityWorker polling... (server=%s:%s domain=%s task_list=%s connid=%s)",
            self.host,
            self.port,
            self.domain,
            self.task_list,
            self.service.connection.current_id,
        )

        while not self.shutdown_event.is_set():
            try:
                self._poll()
            except StopRequestedException:
                break
            except PollError as err:
                logger.warning(
                    "Worker error: %s (%s) - retrying...", err, err.__class__.__name__
                )
                time.sleep(0.1)
                continue
            except Exception as err:
                # Here we can see things like TChannelException, EOFError...
                # Raise UnretryableError if you want to stop retrying.
                logger.warning(
                    "Worker error: %s (%s) - retrying...", err, err.__class__.__name__
                )
                raise err

        raise UnretryableError

    def _work_done_callback(self, future):
        try:
            future.result()
        except Exception:
            pass
        finally:
            logger.error("Worker shutdown complete.")

    def _conn_timeout_callback(self, *args, **kwargs):
        if self.shutdown_event.is_set():
            raise StopRequestedException

    def _poll(self):
        req = PollForActivityTaskRequest()
        req.domain = self.domain
        req.identity = WorkflowService.get_identity()
        req.task_list = TaskList(name=self.task_list)
        req.task_list_metadata = TaskListMetadata(max_tasks_per_second=1)

        task: PollForActivityTaskResponse
        task, error = self.service.poll_for_activity_task(req)

        if not task.task_token:
            logger.warning("PollForActivityResponse received but empty")
            raise PollError

        if error:
            logger.warning("PollForActivityTaskRequest failed: %s", error)
            raise PollError

        logger.info(
            "Activity taks received! (activity_id=%s activity_type=%s workflow_type=%s, workflow_domain=%s)",
            task.activity_id,
            task.activity_type,
            task.workflow_type,
            task.workflow_domain,
        )

        try:
            activity = Activity(
                task, self.service, self.package_queue, self.executor, self.workflow
            )
            activity.run()
        except Exception as err:
            logger.warning("Activity execution failed: %s", err, exc_info=True)
            raise PollError

    def stop(self, timeout=None):
        futures.wait((self.future,), timeout=timeout, return_when=futures.ALL_COMPLETED)


class Activity:
    def __init__(self, task, service, package_queue, executor, workflow):
        self.service = service
        self.package_queue = package_queue
        self.executor = executor
        self.workflow = workflow

        self.identity = WorkflowService.get_identity()
        self.task = task

    def run(self):
        logger.info("Running activity: %s", self.task)

        res = None
        try:
            res = self._inner()
        except ActivityError:
            self._fail_task("Activity error", "no details for now")
        except Exception as err:
            logger.warning("Activity raised unexpectedly: %s", err)
            self._fail_task("Unhandled activity exception", f"{err} {type(err)}")
        else:
            self._complete_task(res)

    def _inner(self):
        # Payload lookup
        payload = self._decode(self.task.input)
        name = payload.get("name")
        url = payload.get("url")
        if not name or not url:
            raise ActivityError("Activity task payload is incomplete")

        try:
            package = Package.create_package(
                self.package_queue, self.executor, self.workflow, name, url
            )
        except Exception as err:
            raise ActivityError(f"Package cannot be created: {err}")

        logger.info("Package created! (id=%s)", package.uuid)

        # A3M-TODO: heartbeats!

        while True:
            res = get_package_status(self.package_queue, package.uuid)
            if res == a3m_pb2.COMPLETE:
                break
            if res.status == a3m_pb2.PROCESSING:
                time.sleep(1)
                continue
            if res.status in (a3m_pb2.FAILED, a3m_pb2.REJECTED):
                raise ActivityError("Processing failed")

        return package.uuid

    def _heartbeat_task(self, details=None):
        kwargs = dict(
            task_token=self.task.task_token, identity=WorkflowService.get_identity()
        )
        if details:
            kwargs.update(details=self._encode(details))
        req = RecordActivityTaskHeartbeatRequest(**kwargs)
        return self.service.record_activity_task_heartbeat(req)

    def _fail_task(self, reason, details):
        req = RespondActivityTaskFailedRequest(
            task_token=self.task.task_token,
            identity=WorkflowService.get_identity(),
            reason=self._encode(reason),
            details=self._encode(details),
        )
        self.service.respond_activity_task_failed(req)

    def _complete_task(self, result):
        req = RespondActivityTaskCompletedRequest(
            task_token=self.task.task_token,
            identity=self.identity,
            result=self._encode(result),
        )
        return self.service.respond_activity_task_completed(req)

    def _decode(self, data):
        return json.loads(data)

    def _encode(self, data):
        return json.dumps(data).encode("utf-8")
