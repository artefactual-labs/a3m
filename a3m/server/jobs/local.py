"""
Jobs executed locally in MCPServer.
"""
import abc
import logging

from a3m.server.db import auto_close_old_connections
from a3m.server.jobs.base import Job


logger = logging.getLogger(__name__)


class LocalJob(Job, metaclass=abc.ABCMeta):
    """Base class for jobs that are executed directly."""

    @auto_close_old_connections()
    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)
        logger.debug("Running %s (package %s)", self.description, self.package.uuid)

        # Reload the package, in case the path has changed
        self.package.reload()
        self.save_to_db()