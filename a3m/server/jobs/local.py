"""
Jobs executed locally in MCP server.
"""
import abc
import logging

from a3m.main import models
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


class GetUnitVarLinkJob(LocalJob):
    """Gets the next link in the chain from a UnitVariable.
    """

    # TODO: replace this concept, if possible

    @auto_close_old_connections()
    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)

        try:
            unitvar = models.UnitVariable.objects.get(
                unittype=self.package.unit_variable_type,
                unituuid=self.package.subid,
                variable=self.link.config["variable"],
            )
        except models.UnitVariable.DoesNotExist:
            link_id = self.link.config["chain_id"]
        else:
            link_id = str(unitvar.microservicechainlink)

        try:
            link = self.link.workflow.get_link(link_id)
        except KeyError:
            raise ValueError(
                f"Failed to find workflow link {link_id} (set in unit variable)"
            )

        self.job_chain.next_link = link

        self.mark_complete()

        return next(self.job_chain, None)


class SetUnitVarLinkJob(LocalJob):
    """Sets the unit variable configured in the workflow.
    """

    # TODO: replace this concept, if possible

    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)

        self.package.set_variable(
            self.link.config["variable"],
            self.link.config["variable_value"],
            self.link.config["chain_id"],
        )

        self.mark_complete()

        return next(self.job_chain, None)
