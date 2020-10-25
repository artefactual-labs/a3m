"""
A job corresponds to a microservice, a link in the workflow, and the `Jobs`
table in the database.

Initialization of `Job` objects is typically done via a `JobChain`,
corresponding to a chain in the workflow. The `JobChain` object handles
determining the next job to be run, and passing data between jobs.

The `Job` class is a base class for other job types. There are various
concrete types of jobs, handled by subclasses:
    * `ClientScriptJob`, handling Jobs to be execute on MCPClient
    * `NextLinkDecisionJob`, handling workflow decision points
"""
from a3m.server.jobs.base import Job
from a3m.server.jobs.chain import JobChain
from a3m.server.jobs.client import ClientScriptJob
from a3m.server.jobs.client import DirectoryClientScriptJob
from a3m.server.jobs.client import FilesClientScriptJob
from a3m.server.jobs.decisions import NextLinkDecisionJob

__all__ = (
    "ClientScriptJob",
    "DirectoryClientScriptJob",
    "FilesClientScriptJob",
    "Job",
    "JobChain",
    "NextLinkDecisionJob",
)
