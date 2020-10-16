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
import uuid

from django.db import transaction

from a3m.fileOperations import updateSizeAndChecksum
from a3m.main.models import File


logger = logging.getLogger(__name__)


def main(job, shared_path, file_uuid, file_path, date, event_uuid):
    try:
        File.objects.get(uuid=file_uuid)
    except File.DoesNotExist:
        logger.exception("File with UUID %s cannot be found.", file_uuid)
        return 1

    updateSizeAndChecksum(file_uuid, file_path, date, event_uuid)

    return 0


def call(jobs):
    parser = argparse.ArgumentParser()
    parser.add_argument("sharedPath")
    parser.add_argument(
        "-i", "--fileUUID", type=lambda x: str(uuid.UUID(x)), dest="file_uuid"
    )
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

    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                args = parser.parse_args(job.args[1:])

                job.set_status(
                    main(
                        job,
                        args.sharedPath,
                        args.file_uuid,
                        args.file_path,
                        args.date,
                        args.event_uuid,
                    )
                )
