"""
Built-in task backend. Submits `Task` objects to a local pool of processes for
processing, and returns results.
"""
import logging
import uuid
from concurrent import futures

from a3m.client.mcp import execute_command
from a3m.client.metrics import init_counter_labels
from a3m.server import metrics
from a3m.server.db import auto_close_old_connections
from a3m.server.jobs import Job
from a3m.server.tasks.backends.base import TaskBackend
from a3m.server.tasks.task import Task


logger = logging.getLogger(__name__)


class PoolTaskBatch:
    def __init__(self):
        self.uuid = uuid.uuid4()
        self.tasks = []
        self.future = None

    def __len__(self):
        return len(self.tasks)

    def serialize_task(self, task: Task):
        return {
            "uuid": str(task.uuid),
            "createdDate": task.start_timestamp.isoformat(" "),
            "arguments": task.arguments,
            "wants_output": task.wants_output,
            "execute": task.execute,
        }

    def add_task(self, task: Task):
        self.tasks.append(task)

    @auto_close_old_connections()
    def run(self, job_name: str, batch_payload):
        result = execute_command(job_name, batch_payload)
        return self, result

    def submit(self, executor, job):
        data = {
            "tasks": {str(task.uuid): self.serialize_task(task) for task in self.tasks}
        }

        self.future = executor.submit(self.run, job.name, data)

        logger.debug("Submitted pool job %s (%s)", self.uuid, job.name)

    def save(self, job):
        Task.bulk_log(self.tasks, job)

    def update_task_results(self, results):
        result = results["task_results"]
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


class PoolTaskBackend(TaskBackend):
    """Submits tasks to the pool.

    Tasks are batched into BATCH_SIZE groups (default 128) and sent to the
    client. This adds some complexity but saves a lot of overhead.
    """

    def __init__(self):
        init_counter_labels()

        # Having multiple threads would be equivalent to deploying multiple
        # MCPClient instances in Archivematica which is known to be problematic.
        # Let's stick to one for now.
        self.executor = futures.ThreadPoolExecutor(max_workers=1)

        self.current_task_batches = {}  # job_uuid: PoolTaskBatch
        self.pending_jobs = {}  # job_uuid: List[PoolTaskBatch]
        self.batches_to_submit = {}  # job_uuid: List[PoolTaskBatch]

    def submit_task(self, job: Job, task: Task):
        current_task_batch = self._get_current_task_batch(job.uuid)
        if len(current_task_batch) == 0:
            metrics.gearman_pending_jobs_gauge.inc()

        current_task_batch.add_task(task)

        # If we've hit TASK_BATCH_SIZE, save the batch
        if (len(current_task_batch) % self.TASK_BATCH_SIZE) == 0:
            self._save_batch(job, current_task_batch)

    def wait_for_results(self, job):
        self._submit_batches(job)
        try:
            pending_batches = self.pending_jobs[job.uuid]
        except KeyError:
            # No batches submitted
            return

        # Wait for all batches to complete.
        futs = [item.future for item in pending_batches]
        for future in futures.as_completed(futs):
            batch, results = future.result()
            yield from batch.update_task_results(results)
            metrics.gearman_active_jobs_gauge.dec()

        # Once we've gotten results for all job tasks, clear the batches
        del self.pending_jobs[job.uuid]

    def _get_current_task_batch(self, job_uuid) -> PoolTaskBatch:
        try:
            return self.current_task_batches[job_uuid]
        except KeyError:
            self.current_task_batches[job_uuid] = PoolTaskBatch()
            return self.current_task_batches[job_uuid]

    def _save_batch(self, job, task_batch):
        task_batch.save(job)
        if job.uuid not in self.batches_to_submit:
            self.batches_to_submit[job.uuid] = []
        self.batches_to_submit[job.uuid].append(task_batch)
        del self.current_task_batches[job.uuid]

    def _submit_batches(self, job: Job):
        # Check if we have anything for this job that hasn't been saved
        current_task_batch = self._get_current_task_batch(job.uuid)
        if len(current_task_batch) > 0:
            self._save_batch(job, current_task_batch)

        # Submit all saved batches
        if job.uuid in self.batches_to_submit:
            for task_batch in self.batches_to_submit[job.uuid]:
                self._submit_batch(job, task_batch)

    def _submit_batch(self, job, task_batch):
        if len(task_batch) == 0:
            return

        task_batch.submit(self.executor, job)

        metrics.gearman_active_jobs_gauge.inc()
        metrics.gearman_pending_jobs_gauge.dec()

        if job.uuid not in self.pending_jobs:
            self.pending_jobs[job.uuid] = []
        self.pending_jobs[job.uuid].append(task_batch)

    def shutdown(self, wait=True):
        self.executor.shutdown(wait)
