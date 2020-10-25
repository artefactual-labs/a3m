"""
Jobs remotely executed by on MCP client.
"""
import abc
import logging

from a3m.main import models
from a3m.server import metrics
from a3m.server.db import auto_close_old_connections
from a3m.server.jobs.base import Job
from a3m.server.tasks import get_task_backend
from a3m.server.tasks import Task


logger = logging.getLogger(__name__)


def _escape_for_command_line(value):
    # escape slashes, quotes, backticks
    value = value.replace("\\", "\\\\")
    value = value.replace('"', '\\"')
    value = value.replace("`", r"\`")

    return value


class ClientScriptJob(Job, metaclass=abc.ABCMeta):
    """A job with one or more Tasks."""

    # If True, request stdout/stderr be returned by mcp client in task results
    capture_task_output = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Lazy initialize in `run` method
        self.task_backend = None

        # Exit code is the maximum task exit code; start with None
        self.exit_code = None

        self.command_replacements = {}

    @property
    def name(self):
        """The name of the job, e.g. "normalize_v1.0".

        Passed to MCPClient to determine the task to run.
        """
        return self.link.config.get("execute", "").lower()

    @property
    def execute(self):
        """Command or module for hte task, as defined in the workflow."""
        return self.link.config.get("execute")

    @property
    def arguments(self):
        """Raw arguments for the task, as defined by the workflow prior to
        value replacement.
        """
        return self.link.config.get("arguments")

    @property
    def stdout_file(self):
        """A file path to capture job stdout, as defined in the workflow."""
        return self.link.config.get("stdout_file")

    @property
    def stderr_file(self):
        """A file path to capture job stderr, as defined in the workflow."""
        return self.link.config.get("stderr_file")

    @staticmethod
    def replace_values(command, replacements):
        """Replace variables in a string with any replacements given in a dict.

        A large number of replacement values are available. For more details see
        `get_replacement_mapping` and `get_file_replacement_mapping` in the `packages`
        module.
        """
        if command is None:
            return None

        for key, replacement in replacements.items():
            escaped_replacement = _escape_for_command_line(replacement)
            command = command.replace(key, escaped_replacement)

        return command

    @auto_close_old_connections()
    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)

        logger.debug("Running %s (package %s)", self.description, self.package.uuid)

        # Reload the package, in case the path has changed
        self.package.reload()
        self.save_to_db()

        self.command_replacements = self.package.get_replacement_mapping()
        if self.job_chain.context is not None:
            self.command_replacements.update(self.job_chain.context)

        self.task_backend = get_task_backend()
        self.submit_tasks()
        # Block until out of process tasks have completed
        self.wait_for_task_results()

        self.update_status_from_exit_code()

        return next(self.job_chain, None)

    def submit_tasks(self):
        arguments = self.replace_values(self.arguments, self.command_replacements)
        stdout_file = self.replace_values(self.stdout_file, self.command_replacements)
        stderr_file = self.replace_values(self.stderr_file, self.command_replacements)

        task = Task(
            self.execute,
            arguments,
            stdout_file,
            stderr_file,
            self.command_replacements,
            wants_output=self.capture_task_output,
        )
        self.task_backend.submit_task(self, task)

    def wait_for_task_results(self):
        for task in self.task_backend.wait_for_results(self):
            # A3M-TODO: These 0s avoid comparing int with None
            self.exit_code = max([self.exit_code or 0, task.exit_code or 0])
            metrics.task_completed(task, self)
            self.task_completed_callback(task)

    @abc.abstractmethod
    def task_completed_callback(self, task):
        """Hook for child classes."""

    @auto_close_old_connections()
    def update_status_from_exit_code(self):
        status_code = self.link.get_status_id(self.exit_code)
        models.Job.objects.filter(jobuuid=self.uuid).update(currentstep=status_code)
        if status_code != models.Job.STATUS_COMPLETED_SUCCESSFULLY:
            try:
                status = models.Job.STATUS[status_code][1]
            except IndexError:
                status = status_code
            logger.warning(
                "Processing error in package %s (%s <%s>) with status: %s (job %s).",
                self.package.uuid,
                self.link._src["description"]["en"],
                self.link.id,
                status,
                self.uuid,
            )


class DirectoryClientScriptJob(ClientScriptJob):
    """
    A job with one Task, passing a directory path.
    """

    LINK_END_OF_TRANSFER = "39a128e3-c35d-40b7-9363-87f75091e1ff"

    def task_completed_callback(self, task):
        """Move the package to the Ingest stage."""
        if self.link.id == self.LINK_END_OF_TRANSFER:
            self.package.start_ingest()


class FilesClientScriptJob(ClientScriptJob):
    """
    A job with many tasks, one per file.
    """

    @property
    def filter_subdir(self):
        """Returns directory to filter files on."""
        return self.link.config.get("filter_subdir", "")

    def submit_tasks(self):
        """Iterate through all matching files for the package, and submit tasks."""
        for file_replacements in self.package.files(filter_subdir=self.filter_subdir):
            # File replacement values take priority
            command_replacements = self.command_replacements.copy()
            command_replacements.update(file_replacements)

            arguments = self.replace_values(self.arguments, command_replacements)
            stdout_file = self.replace_values(self.stdout_file, command_replacements)
            stderr_file = self.replace_values(self.stderr_file, command_replacements)

            task = Task(
                self.execute,
                arguments,
                stdout_file,
                stderr_file,
                command_replacements,
                wants_output=self.capture_task_output,
            )
            self.task_backend.submit_task(self, task)
        else:
            # Nothing to do; set exit code to success
            self.exit_code = 0

    def task_completed_callback(self, task):
        pass
