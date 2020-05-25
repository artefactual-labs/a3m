"""
Jobs relating to user decisions.
"""
import abc
import logging
from collections import OrderedDict

from a3m.server.db import auto_close_old_connections
from a3m.server.jobs.base import Job
from a3m.server.processing_config import load_preconfigured_choice
from a3m.server.processing_config import load_processing_xml


logger = logging.getLogger(__name__)


class DecisionJob(Job, metaclass=abc.ABCMeta):
    """A Job that handles a workflow decision point.

    The `run` method checks if a choice has been preconfigured. If so,
    it executes as a normal job. If should fail otherwise.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def workflow(self):
        return self.link.workflow

    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)

        logger.debug("Running %s (package %s)", self.description, self.package.uuid)
        # Reload the package, in case the path has changed
        self.package.reload()
        self.save_to_db()

        preconfigured_choice = self.get_preconfigured_choice()
        if not preconfigured_choice:
            logger.error("Link not configured: %s", self.link.id)
            return

        return self.decide(preconfigured_choice)

    def get_preconfigured_choice(self):
        """Check the processing XML file for a pre-selected choice.

        Returns a value for choices if found, None otherwise.
        """
        return load_preconfigured_choice(
            self.package.current_path, self.link.id, self.workflow
        )

    @abc.abstractmethod
    def get_choices(self):
        """Returns a dict of value: description choices.
        """

    @abc.abstractmethod
    def decide(self, choice):
        """Make a choice, resulting in this job being completed and the
        next one started.
        """


class NextChainDecisionJob(DecisionJob):
    """
    A type of workflow decision that determines the next chain to be executed,
    by UUID.
    """

    def get_choices(self):
        choices = OrderedDict()
        for chain_id in self.link.config["chain_choices"]:
            try:
                chain = self.workflow.get_chain(chain_id)
            except KeyError:
                continue
            choices[chain_id] = chain["description"]

        return choices

    @auto_close_old_connections()
    def decide(self, choice):
        # TODO: fix circular imports :(
        from a3m.server.jobs import JobChain

        if choice not in self.get_choices():
            raise ValueError(f"{choice} is not one of the available choices")

        chain = self.workflow.get_chain(choice)
        logger.debug("Using user selected chain %s for link %s", chain.id, self.link.id)

        self.mark_complete()

        job_chain = JobChain(self.package, chain, self.workflow)
        return next(job_chain, None)


class UpdateContextDecisionJob(DecisionJob):
    """A job that updates the job chain context based on a user choice.
    """

    # TODO: This type of job is mostly copied from the previous
    # linkTaskManagerReplacementDicFromChoice, and it seems to have multiple
    # ways of executing. It could use some cleanup.

    @auto_close_old_connections()
    def run(self, *args, **kwargs):
        # Intentionally don't call super() here
        logger.debug("Running %s (package %s)", self.description, self.package.uuid)
        # Reload the package, in case the path has changed
        self.package.reload()
        self.save_to_db()

        preconfigured_context = self.load_preconfigured_context()
        if not preconfigured_context:
            logger.error("Link not configured: %s", self.link.id)
            return

        logger.debug(
            "Job %s got preconfigured context %s", self.uuid, preconfigured_context
        )
        self.job_chain.context.update(preconfigured_context)
        self.mark_complete()
        return next(self.job_chain, None)

    def _format_items(self, items):
        """Wrap replacement items with the ``%`` wildcard character."""
        return {f"%{key}%": value for key, value in items.items()}

    def load_preconfigured_context(self):
        choice_id = self.link.id

        processing_xml = load_processing_xml(self.package.current_path, self.workflow)
        if processing_xml is None:
            return

        for preconfiguredChoice in processing_xml.findall(".//preconfiguredChoice"):
            if preconfiguredChoice.find("appliesTo").text != choice_id:
                continue
            desired_choice = preconfiguredChoice.find("goToChain").text

            try:
                link = self.workflow.get_link(choice_id)
            except KeyError:
                return None

            for replacement in link.config["replacements"]:
                if replacement["id"] != desired_choice:
                    continue
                # In our JSON-encoded document, the items in
                # the replacements are not wrapped, do it here.
                # Needed by ReplacementDict.
                return self._format_items(replacement["items"])

    def get_choices(self):
        choices = OrderedDict()
        # TODO: this is kind of an odd side effect here; refactor
        self.choice_items = []

        for index, item in enumerate(self.link.config["replacements"]):
            # item description is already translated in workflow
            choices[str(index)] = item["description"]
            self.choice_items.append(self._format_items(item["items"]))

        return choices

    @auto_close_old_connections()
    def decide(self, choice, user_id=None):
        # TODO: DRY with sibling classes
        if choice not in self.get_choices():
            raise ValueError(f"{choice} is not one of the available choices")

        choice_index = int(choice)
        items = self.choice_items[choice_index]

        self.job_chain.context.update(items)
        self.mark_complete()

        return next(self.job_chain, None)
