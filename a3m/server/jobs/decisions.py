"""
Jobs relating to configurable decisions.
"""
import logging

from a3m.server.jobs.base import Job


logger = logging.getLogger(__name__)


class NextLinkDecisionJob(Job):
    """A job that determines the next link to be executed."""

    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)

        logger.debug("Running %s (package %s)", self.description, self.package.uuid)

        # Reload the package, in case the path has changed
        self.package.reload()
        self.save_to_db()

        self.job_chain.next_link = self.decide()

        return next(self.job_chain, None)

    def decide(self):
        config = self.link.config

        config_value = self.get_configured_value(config["config_attr"])
        if config_value is None:
            config_value = config["default"]

        next_id = None
        for item in config["choices"]:
            if item["value"] == config_value:
                next_id = item["link_id"]
                break

        logger.debug("Using user selected link %s", next_id)
        self.mark_complete()

        return next_id

    def get_configured_value(self, attr_name):
        return getattr(self.package.config, attr_name, None)
