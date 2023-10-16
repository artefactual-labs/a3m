from a3m.fpr.registry import FPR
from a3m.fpr.registry import RulePurpose
from a3m.main.models import Event
from a3m.main.models import File
from a3m.main.models import Transfer


def is_extractable(f) -> bool:
    """Determine whether the package is extractable."""
    return len(FPR.get_file_rules(f, purpose=RulePurpose.EXTRACT)) > 0


def already_extracted(f) -> bool:
    """Determine whether the package has already been extracted."""
    # Look for files in a directory that starts with the package name
    files = File.objects.filter(
        transfer=f.transfer,
        currentlocation__startswith=f.currentlocation,
        removedtime__isnull=True,
    ).exclude(uuid=f.uuid)
    # Check for unpacking events that reference the package
    if Event.objects.filter(
        file_uuid__in=files,
        event_type="unpacking",
        event_detail__contains=f.currentlocation,
    ).exists():
        return True
    return False


def main(job, sip_uuid):
    transfer = Transfer.objects.get(uuid=sip_uuid)
    for f in transfer.file_set.filter(removedtime__isnull=True).iterator():
        if is_extractable(f) and not already_extracted(f):
            job.pyprint(
                f.currentlocation,
                "is extractable and has not yet been extracted.",
            )
            return 0
    job.pyprint("No extractable files found.")
    return 1


def call(jobs):
    for job in jobs:
        with job.JobContext():
            job.set_status(main(job, job.args[1]))
