"""
Archivematica Client.

This module knows how to process batches dispatched by the workflow engine. A
batch is made of jobs

This executable does the following.

1. Loads tasks from config. Loads a list of performable tasks (client scripts)
   from a config file (typically that in lib/archivematicaClientModules) and
   creates a mapping from names of those tasks (e.g., 'normalize_v1.0') to the
   names of the Python modules that handle them.

2. Registers tasks with Gearman. Creates a Gearman worker and registers the
   loaded tasks with the Gearman server, effectively saying "Hey, I can
   normalize files", etc.

When the MCPServer requests that the MCPClient perform a registered task, the
MCPClient thread calls ``execute_command``, passing it the Gearman job.  This
gets turned into one or more Job objects, each corresponding to a task on the
MCP Server side.  These jobs are sent in batches to the `call()` function of the
Python module configured to handle the registered task type.

The Python modules doing the work receive the list of jobs and set an exit code,
standard out and standard error for each job.  Only one set of jobs executes at
a time, so each Python module is free to assume it has the whole machine at its
disposal, giving it the option of running subprocesses or multiple threads if
desired.

When a set of jobs is complete, the standard output and error of each is written
back to the database.  The exit code of each job is returned to Gearman and
communicated back to the MCP Server (where it is ultimately used to decide which
task to run next).
"""
# This file is part of Archivematica.
#
# Copyright 2010-2017 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.
import importlib
import logging
import shlex

from django.conf import settings as django_settings
from django.db import transaction

from a3m.client import ASSETS_DIR
from a3m.client import metrics
from a3m.client.job import Job
from a3m.databaseFunctions import auto_close_db
from a3m.databaseFunctions import getUTCDate
from a3m.databaseFunctions import retryOnFailure
from a3m.main.models import Task


logger = logging.getLogger(__name__)

replacement_dict = {
    r"%sharedPath%": django_settings.SHARED_DIRECTORY,
    r"%clientAssetsDirectory%": ASSETS_DIR,
}


@auto_close_db
def handle_batch_task(task_name, batch_payload):
    tasks = batch_payload["tasks"]

    mod = ""
    utc_date = getUTCDate()
    jobs = []
    for task_uuid in tasks:
        task_data = tasks[task_uuid]
        arguments = task_data["arguments"]
        mod = task_data["execute"]

        replacements = list(replacement_dict.items()) + list(
            {
                r"%date%": utc_date.isoformat(),
                r"%taskUUID%": task_uuid,
                r"%jobCreatedDate%": task_data["createdDate"],
            }.items()
        )

        for var, val in replacements:
            arguments = arguments.replace(var, val)

        job = Job(
            task_name,
            task_data["uuid"],
            _parse_command_line(arguments),
            caller_wants_output=task_data["wants_output"],
        )
        jobs.append(job)

    # Set their start times.  If we collide with the MCP Server inserting new
    # Tasks (which can happen under heavy concurrent load), retry as needed.
    def set_start_times():
        Task.objects.filter(taskuuid__in=[item.UUID for item in jobs]).update(
            starttime=utc_date
        )

    retryOnFailure("Set task start times", set_start_times)

    module = importlib.import_module(f"a3m.client.clientScripts.{mod}")
    module.call(jobs)

    return jobs


def _parse_command_line(s):
    return [_shlex_unescape(x) for x in shlex.split(s)]


# If we're looking at an escaped backtick, drop the escape
# character.  Shlex doesn't do this but bash unescaping does, and we
# want to remain compatible.
def _shlex_unescape(s):
    return "".join(c1 for c1, c2 in zip(s, s[1:] + ".") if (c1, c2) != ("\\", "`"))


def fail_all_tasks(batch_payload, reason):
    tasks = batch_payload["tasks"]

    # Give it a best effort to write out an error for each task.  Obviously if
    # we got to this point because the DB is unavailable this isn't going to
    # work...
    try:

        def fail_all_tasks_callback():
            for task_uuid in tasks:
                Task.objects.filter(taskuuid=task_uuid).update(
                    stderror=str(reason), exitcode=1, endtime=getUTCDate()
                )

        retryOnFailure("Fail all tasks", fail_all_tasks_callback)
    except Exception as e:
        logger.exception("Failed to update tasks in DB: %s", e)

    # But we can at least send an exit code back to the server.
    return {"task_results": {task_id: {"exitCode": 1} for task_id in tasks}}


@auto_close_db
def execute_command(task_name: str, batch_payload):
    """Execute the command encoded in ``batch_payload`` and return its exit
    code, standard output and standard error as a dictionary.
    """
    logger.debug("\n\n*** RUNNING TASK: %s", task_name)

    with metrics.task_execution_time_histogram.labels(script_name=task_name).time():
        try:
            jobs = handle_batch_task(task_name, batch_payload)
            results = {}

            def write_task_results_callback():
                with transaction.atomic():
                    for job in jobs:
                        logger.debug("Completed job: %s\n", job.dump())

                        exit_code = job.get_exit_code()
                        end_time = getUTCDate()

                        kwargs = {"exitcode": exit_code, "endtime": end_time}
                        if (
                            django_settings.CAPTURE_CLIENT_SCRIPT_OUTPUT
                            or kwargs["exitcode"] > 0
                        ):
                            kwargs.update(
                                {
                                    "stdout": job.get_stdout(),
                                    "stderror": job.get_stderr(),
                                }
                            )
                        Task.objects.filter(taskuuid=job.UUID).update(**kwargs)

                        results[job.UUID] = {
                            "exitCode": exit_code,
                            "finishedTimestamp": end_time,
                        }

                        if job.caller_wants_output:
                            # Send back stdout/stderr so it can be written to files.
                            # Most cases don't require this (logging to the database is
                            # enough), but the ones that do are coordinated through the
                            # MCP Server so that multiple MCP Client instances don't try
                            # to write the same file at the same time.
                            results[job.UUID]["stdout"] = job.get_stdout()
                            results[job.UUID]["stderror"] = job.get_stderr()

                        if exit_code == 0:
                            metrics.job_completed(task_name)
                        else:
                            metrics.job_failed(task_name)

            retryOnFailure("Write task results", write_task_results_callback)

            return {"task_results": results}
        except SystemExit:
            logger.error(
                "IMPORTANT: Task %s attempted to call exit()/quit()/sys.exit(). This module should be fixed!",
                task_name,
            )
            return fail_all_tasks(batch_payload, "Module attempted exit")
        except Exception as e:
            logger.exception("Exception while processing task %s: %s", task_name, e)
            return fail_all_tasks(batch_payload, e)
