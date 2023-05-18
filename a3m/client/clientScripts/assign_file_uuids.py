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
"""Assign a UUID to each file in the target directory.

This client script assigns a UUID to a file by generating a new UUID and
creating several database rows (model instances), among them a ``File``
instance recording the UUID associated to a unit model, i.e., to a ``Transfer``
or ``SIP`` instance. ``Event`` instances are also created for "ingestion" and
"accession" events.

Salient parameters are the UUID of the containing unit (Transfer or SIP), the
path to the SIP directory, and the subdirectory being targeted if any.

"""
import argparse
import logging
import os
import uuid

from django.db import transaction

from a3m.archivematicaFunctions import chunk_iterable
from a3m.fileOperations import addFileToSIP
from a3m.fileOperations import addFileToTransfer
from a3m.main.models import File

logger = logging.getLogger(__name__)


TRANSFER = "Transfer"
SIP = "SIP"


def get_transfer_file_queryset(transfer_uuid):
    """Return a queryset for File objects related to the Transfer."""
    return File.objects.filter(transfer=transfer_uuid)


def assign_transfer_file_uuid(
    job,
    file_path,
    target_dir,
    date="",
    event_uuid=None,
    sip_directory="",
    transfer_uuid=None,
    sip_uuid=None,
    use="original",
    update_use=True,
    filter_subdir=None,
):
    """Walk transaction directory and write files to database.

    If files are in a re-ingested Archivematica AIP, parse the METS
    file and reuse existing information. Otherwise, create a new UUID.

    We open a database transaction for each chunk of 10 files, in an
    attempt to balance performance with reasonable transaction lengths.
    """
    if isinstance(file_path, bytes):
        file_path = file_path.decode("utf-8")

    file_path_relative_to_sip = file_path.replace(
        sip_directory, "%transferDirectory%", 1
    )
    event_type = "ingestion"
    file_uuid = str(uuid.uuid4())
    job.print_output(f"Generated UUID for file {file_uuid}")

    addFileToTransfer(
        file_path_relative_to_sip,
        file_uuid,
        transfer_uuid,
        event_uuid,
        date,
        use=use,
        sourceType=event_type,
    )


def assign_sip_file_uuid(
    job,
    file_path,
    target_dir,
    date="",
    event_uuid=None,
    sip_directory="",
    transfer_uuid=None,
    sip_uuid=None,
    use="original",
    update_use=True,
    filter_subdir=None,
):
    """Write SIP file to database with new UUID."""
    if isinstance(file_path, bytes):
        file_path = file_path.decode("utf-8")

    file_uuid = str(uuid.uuid4())
    file_path_relative_to_sip = file_path.replace(sip_directory, "%SIPDirectory%", 1)

    matching_file = File.objects.filter(
        currentlocation=file_path_relative_to_sip,
        sip=sip_uuid,
    ).first()
    if matching_file:
        job.print_error(f"File already has UUID: {matching_file.uuid}")
        if update_use:
            matching_file.filegrpuse = use
            matching_file.save()
        return

    job.print_output(f"Generated UUID for file {file_uuid}.")
    addFileToSIP(
        file_path_relative_to_sip,
        file_uuid,
        sip_uuid,
        event_uuid,
        date,
        use=use,
    )


def assign_uuids_to_files_in_dir(**kwargs):
    """Walk target directory and write files to database with new UUID.

    We open a database transaction for each chunk of 10 files, in an
    attempt to balance performance with reasonable transaction lengths.
    """
    target_dir = kwargs["target_dir"]
    transfer_uuid = kwargs["transfer_uuid"]
    for root, _, filenames in os.walk(target_dir):
        for file_chunk in chunk_iterable(filenames):
            with transaction.atomic():
                for filename in file_chunk:
                    if not filename:
                        continue
                    kwargs["file_path"] = os.path.join(root, filename)
                    if transfer_uuid:
                        assign_transfer_file_uuid(**kwargs)
                    else:
                        assign_sip_file_uuid(**kwargs)
    return 0


def call(jobs):
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--date", action="store", dest="date", default="")
    parser.add_argument(
        "-u",
        "--eventIdentifierUUID",
        type=uuid.UUID,
        dest="event_uuid",
    )
    parser.add_argument(
        "-s", "--sipDirectory", action="store", dest="sip_directory", default=""
    )
    parser.add_argument("-S", "--sipUUID", type=uuid.UUID, dest="sip_uuid")
    parser.add_argument("-T", "--transferUUID", type=uuid.UUID, dest="transfer_uuid")
    parser.add_argument("-e", "--use", action="store", dest="use", default="original")
    parser.add_argument(
        "--filterSubdir", action="store", dest="filter_subdir", default=None
    )
    parser.add_argument(
        "--disable-update-filegrpuse",
        action="store_false",
        dest="update_use",
        default=True,
    )

    for job in jobs:
        with job.JobContext(logger=logger):
            kwargs = vars(parser.parse_args(job.args[1:]))
            kwargs["job"] = job

            TRANSFER_SIP_UUIDS = [kwargs["sip_uuid"], kwargs["transfer_uuid"]]
            if all(TRANSFER_SIP_UUIDS) or not any(TRANSFER_SIP_UUIDS):
                job.print_error("SIP exclusive-or Transfer UUID must be defined")
                job.set_status(2)
                return

            kwargs["target_dir"] = kwargs["sip_directory"]
            if kwargs["filter_subdir"]:
                kwargs["target_dir"] = os.path.join(
                    kwargs["sip_directory"], kwargs["filter_subdir"]
                )

            job.set_status(assign_uuids_to_files_in_dir(**kwargs))
