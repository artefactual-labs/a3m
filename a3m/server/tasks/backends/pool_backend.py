"""
Built-in task backend. Submits `Task` objects to a local pool of processes for
processing, and returns results.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import concurrent.futures
import logging
import uuid

import six
from django.conf import settings
from six.moves import cPickle

from a3m.client.mcp import execute_command
from a3m.client.mcp import get_supported_modules
from a3m.server import metrics
from a3m.server.tasks.backends.base import TaskBackend
from a3m.server.tasks.task import Task


logger = logging.getLogger("archivematica.mcp.server.jobs.tasks")


class PoolTaskBackend(TaskBackend):
    """Submits tasks to the pool.

    Tasks are batched into BATCH_SIZE groups (default 128), pickled and sent to
    MCPClient. This adds some complexity but saves a lot of overhead.

    TODO: should use a ProcessPoolExecutor?
    TODO: factor out code shared with GearmanTaskBackend.
    """

    def __init__(self):
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=settings.WORKER_THREADS
        )
        self.supported_modules = get_supported_modules()

        self.current_task_batches = {}  # job_uuid: PoolTaskBatch
        self.pending_gearman_jobs = {}  # job_uuid: List[PoolTaskBatch]

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
            pending_batches = self.pending_gearman_jobs[job.uuid]
        except KeyError:
            # No batches submitted
            return

        # Wait for all batches to complete.
        futures = [item.future for item in pending_batches]
        for future in concurrent.futures.as_completed(futures):
            batch, results = future.result()
            for task in batch.update_task_results(results):
                yield task
            metrics.gearman_active_jobs_gauge.dec()

        # Once we've gotten results for all job tasks, clear the batches
        del self.pending_gearman_jobs[job.uuid]

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

        if job.uuid not in self.pending_gearman_jobs:
            self.pending_gearman_jobs[job.uuid] = []
        self.pending_gearman_jobs[job.uuid].append(task_batch)

        # Clear the current task batch
        if self.current_task_batches[job.uuid] is task_batch:
            del self.current_task_batches[job.uuid]


class PoolTaskBatch(object):
    def __init__(self):
        self.uuid = uuid.uuid4()
        self.tasks = []
        self.future = None

    def __len__(self):
        return len(self.tasks)

    def serialize_task(self, task):
        return {
            "uuid": six.text_type(task.uuid),
            "createdDate": task.start_timestamp.isoformat(b" "),
            "arguments": task.arguments,
            "wants_output": task.wants_output,
        }

    def add_task(self, task):
        self.tasks.append(task)

    def run(self, supported_modules, job_name, payload):
        gearman_job = FakeGearmanJob(job_name, payload)
        result = execute_command(supported_modules, None, gearman_job)
        return self, result

    def submit(self, executor, supported_modules, job):
        # Log tasks to DB, before submitting the batch, as mcpclient then updates them
        Task.bulk_log(self.tasks, job)

        data = {"tasks": {}}
        for task in self.tasks:
            task_uuid = six.text_type(task.uuid)
            data["tasks"][task_uuid] = self.serialize_task(task)

        pickled_data = cPickle.dumps(data)

        self.future = executor.submit(
            self.run, supported_modules, six.binary_type(job.name), pickled_data
        )

        logger.debug("Submitted gearman job %s (%s)", self.uuid, job.name)

    def update_task_results(self, results):
        result = cPickle.loads(results)["task_results"]
        for task in self.tasks:
            task_id = six.text_type(task.uuid)
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
