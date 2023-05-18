# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
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
import argparse
import logging
import os
import uuid

from django.db import transaction

from a3m.archivematicaFunctions import chunk_iterable
from a3m.fileOperations import updateSizeAndChecksum
from a3m.main.models import File


logger = logging.getLogger(__name__)

SIP_REPLACEMENT_PATH_STRING = r"%SIPDirectory%"
TRANSFER_REPLACEMENT_PATH_STRING = r"%transferDirectory%"


def _filter_queryset_by_subdir(queryset, replacement_path_string, filter_subdir):
    """Filter queryset by filter_subdir."""
    filter_path = "".join([replacement_path_string, filter_subdir])
    return queryset.filter(currentlocation__startswith=filter_path)


def get_transfer_file_queryset(transfer_uuid, filter_subdir):
    """Return Queryset of files in this transfer."""
    files = File.objects.filter(transfer=transfer_uuid)
    if filter_subdir:
        files = _filter_queryset_by_subdir(
            files, TRANSFER_REPLACEMENT_PATH_STRING, filter_subdir
        )
    return files


def get_sip_file_queryset(sip_uuid, filter_subdir):
    """Return Queryset of files in this SIP."""
    files = File.objects.filter(sip=sip_uuid)
    if filter_subdir:
        files = _filter_queryset_by_subdir(
            files, SIP_REPLACEMENT_PATH_STRING, filter_subdir
        )
    return files


def update_size_and_checksum_for_file(
    job,
    file_,
    sip_directory,
    transfer_uuid,
    date,
    event_uuid,
):
    """Update size and checksum for file in database.

    If file is from Archivematica AIP transfer, try to extract and use
    the size, checksum, and checksum type values from the METS.
    """
    kw = {}
    if transfer_uuid:
        file_path = file_.currentlocation.replace(
            TRANSFER_REPLACEMENT_PATH_STRING, sip_directory
        )
    else:
        file_path = file_.currentlocation.replace(
            SIP_REPLACEMENT_PATH_STRING, sip_directory
        )

    if not os.path.exists(file_path):
        return

    job.print_output(f"Updating file size and checksum for file {file_.uuid}")
    updateSizeAndChecksum(file_.uuid, file_path, date, event_uuid, **kw)


def update_files(
    job,
    files,
    sip_directory,
    transfer_uuid,
    date,
    event_uuid,
):
    """Update file sizes and checksums for each file in list.

    We open a database transaction for each chunk of 10 files, in an
    attempt to balance performance with reasonable transaction lengths.
    """
    for file_chunk in chunk_iterable(files):
        with transaction.atomic():
            for file_ in file_chunk:
                if not file_:
                    continue
                update_size_and_checksum_for_file(
                    job,
                    file_,
                    sip_directory,
                    transfer_uuid,
                    date,
                    event_uuid,
                )

    return 0


def call(jobs):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--sipDirectory", action="store", dest="sip_directory", default=""
    )
    parser.add_argument("-S", "--sipUUID", type=uuid.UUID, dest="sip_uuid")
    parser.add_argument("-T", "--transferUUID", type=uuid.UUID, dest="transfer_uuid")
    parser.add_argument("-d", "--date", action="store", dest="date", default="")
    parser.add_argument(
        "--filterSubdir", action="store", dest="filter_subdir", default=None
    )
    parser.add_argument(
        "-u",
        "--eventIdentifierUUID",
        type=uuid.UUID,
        dest="event_uuid",
    )

    for job in jobs:
        with job.JobContext(logger=logger):
            args = parser.parse_args(job.args[1:])

            TRANSFER_SIP_UUIDS = [args.sip_uuid, args.transfer_uuid]
            if all(TRANSFER_SIP_UUIDS) or not any(TRANSFER_SIP_UUIDS):
                job.print_error("SIP exclusive-or Transfer UUID must be defined")
                job.set_status(2)
                return

            files = get_transfer_file_queryset(args.transfer_uuid, args.filter_subdir)
            if args.sip_uuid:
                files = get_sip_file_queryset(args.sip_uuid, args.filter_subdir)

            job.set_status(
                update_files(
                    job,
                    files,
                    args.sip_directory,
                    args.transfer_uuid,
                    args.date,
                    args.event_uuid,
                )
            )
