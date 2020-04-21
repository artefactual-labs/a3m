import os
import sys

from django.db import transaction

from a3m import databaseFunctions
from a3m.main.models import File


def recursivelyRemoveEmptyDirectories(job, dir):
    error_count = 0
    for root, dirs, files in os.walk(dir, topdown=False):
        for directory in dirs:
            try:
                os.rmdir(os.path.join(root, directory))
            except OSError as e:
                job.pyprint(
                    f"{directory} could not be deleted: {e.args}", file=sys.stderr
                )
                error_count += 1
    return error_count


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                SIPDirectory = job.args[1]
                manual_normalization_dir = os.path.join(
                    SIPDirectory, "objects", "manualNormalization"
                )

                errorCount = 0

                if os.path.isdir(manual_normalization_dir):
                    # Delete normalization.csv if present
                    normalization_csv = os.path.join(
                        manual_normalization_dir, "normalization.csv"
                    )
                    if os.path.isfile(normalization_csv):
                        os.remove(normalization_csv)
                        # Need SIP UUID to get file UUID to remove file in DB
                        sipUUID = SIPDirectory[-37:-1]  # Account for trailing /

                        f = File.objects.get(
                            removedtime__isnull=True,
                            originallocation__endswith="normalization.csv",
                            sip_id=sipUUID,
                        )
                        databaseFunctions.fileWasRemoved(f.uuid)

                    # Recursively delete empty manual normalization dir
                    try:
                        errorCount += recursivelyRemoveEmptyDirectories(
                            job, manual_normalization_dir
                        )
                        os.rmdir(manual_normalization_dir)
                    except OSError as e:
                        job.pyprint(
                            "{} could not be deleted: {}".format(
                                manual_normalization_dir, e.args
                            ),
                            file=sys.stderr,
                        )
                        errorCount += 1

                job.set_status(errorCount)
