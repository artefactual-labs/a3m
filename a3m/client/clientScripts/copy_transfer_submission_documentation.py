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
import os
import shutil

from a3m.archivematicaFunctions import find_transfer_path_from_ingest
from a3m.bag import is_bag
from a3m.main.models import File


def call(jobs):
    for job in jobs:
        with job.JobContext():
            sipUUID = job.args[1]
            submissionDocumentationDirectory = job.args[2]
            sharedPath = job.args[3]

            transfer_locations = (
                File.objects.filter(
                    removedtime__isnull=True,
                    sip_id=sipUUID,
                    transfer__currentlocation__isnull=False,
                )
                .values_list("transfer__currentlocation", flat=True)
                .distinct()
            )

            for transferLocation in transfer_locations:
                transferNameUUID = os.path.basename(os.path.abspath(transferLocation))
                transferLocation = find_transfer_path_from_ingest(
                    transferLocation, sharedPath
                )
                job.pyprint("Transfer found in", transferLocation)

                src = os.path.join(
                    transferLocation, "metadata", "submissionDocumentation"
                )
                dst = os.path.join(
                    submissionDocumentationDirectory, "transfer-%s" % (transferNameUUID)
                )

                if is_bag(transferLocation):
                    src = os.path.join(
                        transferLocation,
                        "data",
                        "metadata",
                        "submissionDocumentation",
                    )
                job.pyprint(src, " -> ", dst)
                shutil.copytree(src, dst)
