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
"""Assign a UUID to the passed-in file.

This client script assigns a UUID to a file by generating a new UUID and
creating several database rows (model instances), among them a ``File``
instance recording the UUID associated to a unit model, i.e., to a ``Transfer``
or ``SIP`` instance. ``Event`` instances are also created for "ingestion" and
"accession" events.

Salient parameters are the UUID of the containing unit (Transfer or SIP) and
the path to the file.

"""
import argparse
import logging
import uuid

from django.db import transaction

from a3m.fileOperations import addFileToSIP
from a3m.fileOperations import addFileToTransfer
from a3m.main.models import File

logger = logging.getLogger(__name__)


def main(
    job,
    file_uuid=None,
    file_path="",
    date="",
    event_uuid=None,
    sip_directory="",
    sip_uuid=None,
    transfer_uuid=None,
    use="original",
    update_use=True,
):
    if file_uuid == "None":
        file_uuid = None
    if file_uuid:
        logger.error("File already has UUID: %s", file_uuid)
        if update_use:
            File.objects.filter(uuid=file_uuid).update(filegrpuse=use)
        return 0

    # Stop if both or neither of them are used
    if all([sip_uuid, transfer_uuid]) or not any([sip_uuid, transfer_uuid]):
        logger.error("SIP exclusive-or Transfer UUID must be defined")
        return 2

    # Transfer
    if transfer_uuid:
        file_path_relative_to_sip = file_path.replace(
            sip_directory, "%transferDirectory%", 1
        )
        event_type = "ingestion"
        if not file_uuid:
            file_uuid = str(uuid.uuid4())
            logger.debug("Generated UUID for this file: %s.", file_uuid)
        addFileToTransfer(
            file_path_relative_to_sip,
            file_uuid,
            transfer_uuid,
            event_uuid,
            date,
            use=use,
            sourceType=event_type,
        )
        return 0

    # Ingest
    if sip_uuid:
        file_uuid = str(uuid.uuid4())
        file_path_relative_to_sip = file_path.replace(
            sip_directory, "%SIPDirectory%", 1
        )
        addFileToSIP(
            file_path_relative_to_sip, file_uuid, sip_uuid, event_uuid, date, use=use
        )
        return 0


def call(jobs):
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--fileUUID", type=str, dest="file_uuid")
    parser.add_argument(
        "-p", "--filePath", action="store", dest="file_path", default=""
    )
    parser.add_argument("-d", "--date", action="store", dest="date", default="")
    parser.add_argument(
        "-u",
        "--eventIdentifierUUID",
        type=lambda x: str(uuid.UUID(x)),
        dest="event_uuid",
    )
    parser.add_argument(
        "-s", "--sipDirectory", action="store", dest="sip_directory", default=""
    )
    parser.add_argument(
        "-S", "--sipUUID", type=lambda x: str(uuid.UUID(x)), dest="sip_uuid"
    )
    parser.add_argument(
        "-T", "--transferUUID", type=lambda x: str(uuid.UUID(x)), dest="transfer_uuid"
    )
    parser.add_argument("-e", "--use", action="store", dest="use", default="original")
    parser.add_argument(
        "--disable-update-filegrpuse",
        action="store_false",
        dest="update_use",
        default=True,
    )

    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                args = vars(parser.parse_args(job.args[1:]))
                args["job"] = job

                job.set_status(main(**(args)))
