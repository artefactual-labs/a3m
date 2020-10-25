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
"""Assign UUIDs to all directories in a unit, i.e., Transfer.

This client script assigns a UUID to all subdirectories of a Transfer by
generating a new UUID for each and recording that UUID in a ``Directory``
database row (model instance).

Command-line arguments are the path to the Transfer and the Transfer's UUID. If
the --include-dirs option is something other than 'Yes', the script will exit
without doing anything.

"""
import argparse
import logging
import os
from functools import wraps

from django.db import transaction

from a3m.archivematicaFunctions import format_subdir_path
from a3m.archivematicaFunctions import get_dir_uuids
from a3m.main.models import Directory
from a3m.main.models import Transfer

logger = logging.getLogger(__name__)


class DirsUUIDsException(Exception):
    """If I am raised, return 1."""

    exit_code = 1


class DirsUUIDsWarning(Exception):
    """If I am raised, return 0."""

    exit_code = 0


def exit_on_known_exception(func):
    """Decorator that makes this module's ``main`` function cleaner by handling
    early exiting by catching particular exceptions.
    """

    @wraps(func)
    def wrapped(*_args, **kwargs):
        try:
            func(*_args, **kwargs)
        except (DirsUUIDsException, DirsUUIDsWarning) as exc:
            return exc.exit_code

    return wrapped


def _get_transfer_mdl(transfer_uuid):
    """Get the ``Transfer`` model with UUID ``transfer_uuid``. Also update it
    in the db to indicate that this transfer has UUIDs assigned to the
    directories that it contains.
    """
    try:
        transfer_mdl = Transfer.objects.get(uuid=transfer_uuid)
        transfer_mdl.diruuids = True
        transfer_mdl.save()
        return transfer_mdl
    except Transfer.DoesNotExist:
        logger.warning("There is no transfer with UUID %s", transfer_uuid)
        raise DirsUUIDsException


def _get_subdir_paths(root_path):
    """Return a generator of subdirectory paths in ``root_path``."""
    if not os.path.isdir(root_path):
        logger.warning("Transfer path %s is not a path to a directory", root_path)
        raise DirsUUIDsException
    # objects/ and root dirs need no UUIDs.
    exclude_paths = (root_path, os.path.join(root_path, "objects"))
    return (
        format_subdir_path(dir_path, root_path)
        for dir_path, __, ___ in os.walk(root_path)
        if dir_path not in exclude_paths
    )


@exit_on_known_exception
def main(job, transfer_path, transfer_uuid):
    """Assign UUIDs to all of the directories (and subdirectories, i.e., all
    unique directory paths) in the absolute system path ``transfer_path``, such
    being the root directory of the transfer with UUID ``transfer_uuid``.
    """
    Directory.create_many(
        get_dir_uuids(_get_subdir_paths(transfer_path), logger, printfn=job.pyprint),
        _get_transfer_mdl(transfer_uuid),
    )
    return 0


def call(jobs):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "transfer_path", type=str, help="The path to the Transfer on disk."
    )
    parser.add_argument("transfer_uuid", type=str, help="The UUID of the Transfer.")
    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                args = parser.parse_args(job.args[1:])
                logger.debug(
                    "assignUUIDsToDirectories called with args: %s", vars(args)
                )
                job.set_status(main(job, **vars(args)))
