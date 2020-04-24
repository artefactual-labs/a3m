"""
Built-in task backend. Submits `Task` objects to a local pool of processes for
processing, and returns results.
"""
import concurrent
import logging
import pickle
import uuid

from a3m.client.mcp import execute_command
from a3m.client.mcp import get_supported_modules
from a3m.server import metrics
from a3m.server.db import auto_close_old_connections
from a3m.server.tasks.backends.base import TaskBackend
from a3m.server.tasks.task import Task


logger = logging.getLogger(__name__)


class PoolTaskBackend(TaskBackend):
    """Submits tasks to the pool.

    Tasks are batched into BATCH_SIZE groups (default 128), pickled and sent to
    MCPClient. This adds some complexity but saves a lot of overhead.

    TODO: factor out code shared with GearmanTaskBackend.
    """

    def __init__(self):
        # Having multiple threads would be equivalent to deploying multiple
        # MCPClient instances in Archivematica which is known to be problematic.
        # Let's stick to one for now.
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.supported_modules = get_supported_modules()

        self.current_task_batches = {}  # job_uuid: PoolTaskBatch
        self.pending_jobs = {}  # job_uuid: List[PoolTaskBatch]

    def submit_task(self, job, task):
        current_task_batch = self._get_current_task_batch(job.uuid)
        if len(current_task_batch) == 0:
            metrics.gearman_pending_jobs_gauge.inc()

        current_task_batch.add_task(task)

        # If we've hit TASK_BATCH_SIZE, send the batch to gearman
        if (len(current_task_batch) % self.TASK_BATCH_SIZE) == 0:
            self._submit_batch(job, current_task_batch)

    def wait_for_results(self, job):
        # Check if we have anything for this job that hasn't been submitted
        current_task_batch = self._get_current_task_batch(job.uuid)
        if len(current_task_batch) > 0:
            self._submit_batch(job, current_task_batch)

        try:
            pending_batches = self.pending_jobs[job.uuid]
        except KeyError:
            # No batches submitted
            return

        # Wait for all batches to complete.
        futures = [item.future for item in pending_batches]
        for future in concurrent.futures.as_completed(futures):
            batch, results = future.result()
            yield from batch.update_task_results(results)
            metrics.gearman_active_jobs_gauge.dec()

        # Once we've gotten results for all job tasks, clear the batches
        del self.pending_jobs[job.uuid]

    def _get_current_task_batch(self, job_uuid):
        try:
            return self.current_task_batches[job_uuid]
        except KeyError:
            self.current_task_batches[job_uuid] = PoolTaskBatch()
            return self.current_task_batches[job_uuid]

    def _submit_batch(self, job, task_batch):
        if len(task_batch) == 0:
            return

        task_batch.submit(self.executor, self.supported_modules, job)

        metrics.gearman_active_jobs_gauge.inc()
        metrics.gearman_pending_jobs_gauge.dec()

        if job.uuid not in self.pending_jobs:
            self.pending_jobs[job.uuid] = []
        self.pending_jobs[job.uuid].append(task_batch)

        # Clear the current task batch
        if self.current_task_batches[job.uuid] is task_batch:
            del self.current_task_batches[job.uuid]

    def shutdown(self, wait=True):
        self.executor.shutdown(wait)


class PoolTaskBatch:
    def __init__(self):
        self.uuid = uuid.uuid4()
        self.tasks = []
        self.future = None

    def __len__(self):
        return len(self.tasks)

    def serialize_task(self, task):
        return {
            "uuid": str(task.uuid),
            "createdDate": task.start_timestamp.isoformat(" "),
            "arguments": task.arguments,
            "wants_output": task.wants_output,
        }

    def add_task(self, task):
        self.tasks.append(task)

    @auto_close_old_connections()
    def run(self, supported_modules, job_name, payload):
        gearman_job = FakeGearmanJob(job_name, payload)
        result = execute_command(supported_modules, None, gearman_job)
        return self, result

    def submit(self, executor, supported_modules, job):
        # Log tasks to DB, before submitting the batch, as mcpclient then updates them
        Task.bulk_log(self.tasks, job)

        data = {"tasks": {}}
        for task in self.tasks:
            task_uuid = str(task.uuid)
            data["tasks"][task_uuid] = self.serialize_task(task)

        pickled_data = pickle.dumps(data)

        self.future = executor.submit(
            self.run, supported_modules, job.name.encode("utf8"), pickled_data
        )

        logger.debug("Submitted pool job %s (%s)", self.uuid, job.name)

    def update_task_results(self, results):
        result = pickle.loads(results)["task_results"]
        for task in self.tasks:
            task_id = str(task.uuid)
            task_result = result[task_id]
            task.exit_code = task_result["exitCode"]
            task.stdout = task_result.get("stdout", "")
            task.stderr = task_result.get("stderr", "")
            task.finished_timestamp = task_result.get("finishedTimestamp")
            task.write_output()

            task.done = True

            logger.debug(
                "Task %s finished! Result %s", task_id, task_result["exitCode"]
            )

            yield task


class FakeGearmanJob:
    def __init__(self, task, data):
        self.task = task
        self.data = data
