import os
import shutil
import sys
from pathlib import Path

from django.conf import settings
from django.db import transaction

from a3m import archivematicaFunctions
from a3m.main.models import Directory
from a3m.main.models import File
from a3m.main.models import SIP


def main(job, transfer_id, sip_id):
    processing_dir = Path(settings.PROCESSING_DIRECTORY)
    transfer_dir = processing_dir / "transfer" / transfer_id
    objects_dir = transfer_dir / "objects"
    sip_dir = processing_dir / "ingest" / sip_id

    archivematicaFunctions.create_structured_directory(sip_dir)

    # Find out if any ``Directory`` models were created for the source
    # ``Transfer``. If so, this fact gets recorded in the new ``SIP`` model.
    dir_mdls = Directory.objects.filter(
        transfer_id=transfer_id,
        currentlocation__startswith="%transferDirectory%objects",
    )
    diruuids = dir_mdls.count() > 0

    # Update model
    sip = SIP.objects.get(pk=sip_id)
    sip.diruuids = diruuids
    sip.save()

    # Move objects to SIP
    for item in os.listdir(str(objects_dir)):
        src_path = os.path.join(str(objects_dir), item)
        dst_path = os.path.join(str(sip_dir), "objects", item)
        # If dst_path already exists and is a directory, shutil.move
        # will move src_path into it rather than overwriting it;
        # to avoid incorrectly-nested paths, move src_path's contents
        # into it instead.
        if os.path.exists(dst_path) and os.path.isdir(src_path):
            for subitem in os.listdir(src_path):
                shutil.move(os.path.join(src_path, subitem), dst_path)
        else:
            shutil.move(src_path, dst_path)

    # Get the ``Directory`` models representing the subdirectories in the
    # objects/ directory. For each subdirectory, confirm it's in the SIP
    # objects/ directory, and update the current location and owning SIP.
    for dir_mdl in dir_mdls:
        currentPath = dir_mdl.currentlocation
        currentSIPDirPath = currentPath.replace(
            "%transferDirectory%", str(sip_dir) + os.sep
        )
        if os.path.isdir(currentSIPDirPath):
            dir_mdl.currentlocation = currentPath.replace(
                "%transferDirectory%", "%SIPDirectory%"
            )
            dir_mdl.sip = sip
            dir_mdl.save()
        else:
            job.pyprint("Directory not found: ", currentSIPDirPath, file=sys.stderr)

    # Get the database list of files in the objects directory.
    # For each file, confirm it's in the SIP objects directory, and update the
    # current location/ owning SIP'
    files = File.objects.filter(
        transfer_id=transfer_id,
        currentlocation__startswith="%transferDirectory%objects",
        removedtime__isnull=True,
    )
    for f in files:
        currentPath = f.currentlocation
        currentSIPFilePath = currentPath.replace(
            "%transferDirectory%", str(sip_dir) + os.sep
        )
        if os.path.isfile(currentSIPFilePath):
            f.currentlocation = currentPath.replace(
                "%transferDirectory%", "%SIPDirectory%"
            )
            f.sip = sip
            f.save()
        else:
            job.pyprint("File not found: ", currentSIPFilePath, file=sys.stderr)

    archivematicaFunctions.create_directories(
        archivematicaFunctions.MANUAL_NORMALIZATION_DIRECTORIES, basepath=str(sip_dir)
    )

    # Copy the JSON metadata file, if present; this contains a
    # serialized copy of DC metadata entered in the dashboard UI
    # during the transfer.
    src = transfer_dir / "metadata" / "dc.json"
    if src.exists():
        dst = sip_dir / "metadata" / "dc.json"
        shutil.copy(str(src), str(dst))


def call(jobs):
    with transaction.atomic():
        job = jobs[0]
        with job.JobContext():
            transfer_id = job.args[1]
            sip_id = job.args[2]

            job.set_status(main(job, transfer_id, sip_id))
