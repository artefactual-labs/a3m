"""Shared directory setup.
"""
import logging
import os
import shutil

from django.conf import settings


logger = logging.getLogger(__name__)


def create():
    dirs = (
        "currentlyProcessing/transfer",
        "currentlyProcessing/ingest",
        "completed",
        "failed",
        "policies",
        "tmp",
    )
    for dirname in dirs:
        dirname = os.path.join(settings.SHARED_DIRECTORY, dirname)
        if os.path.isdir(dirname):
            continue
        logger.debug("Creating directory: %s", dirname)
        os.makedirs(dirname, mode=0o770)


def empty():
    dirs = (
        "currentlyProcessing",
        "completed",
        "failed",
        "policies",
        "tmp",
    )
    for dirname in dirs:
        dirname = os.path.join(settings.SHARED_DIRECTORY, dirname)
        if os.path.isdir(dirname):
            logger.debug("Removing directory and contents: %s", dirname)
            shutil.rmtree(dirname, ignore_errors=True)
