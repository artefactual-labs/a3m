import argparse

from django.db import transaction

from a3m.client import metrics
from a3m.main.models import Transfer


FAILED = "fail"


def main(job, transfer_uuid):
    transfer = Transfer.objects.get(uuid=transfer_uuid)
    metrics.transfer_failed(transfer.type, FAILED)

    return 0


def call(jobs):
    parser = argparse.ArgumentParser(description="Cleanup from failed Transfers.")
    parser.add_argument("transfer_uuid", help="%SIPUUID%")

    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                args = parser.parse_args(job.args[1:])
                job.set_status(main(job, args.transfer_uuid))
