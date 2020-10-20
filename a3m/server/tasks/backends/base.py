import abc

from django.conf import settings


class TaskBackend(metaclass=abc.ABCMeta):
    """Handles out of process `Task` execution."""

    # The number of files we'll pack into each MCP Client job.  Chosen somewhat
    # arbitrarily, but benchmarking with larger values (like 512) didn't make
    # much difference to throughput.
    #
    # Setting this too large will use more memory; setting it too small will
    # hurt throughput.  So the trick is to set it juuuust right.
    TASK_BATCH_SIZE = settings.BATCH_SIZE

    @abc.abstractmethod
    def submit_task(self, job, task):
        """Submit a task as part of the job given, for offline processing."""

    @abc.abstractmethod
    def wait_for_results(self, job):
        """Generator that yields `Task` objects related to the job given,
        as they are processed by the backend.

        This method should only be called once all tasks related to the job
        have been submitted, via `submit_task`.

        Note that task objects are not necessarily returned in the order
        they were submitted.
        """

    def shutdown(self, wait=True):
        """Shut down the backend."""
