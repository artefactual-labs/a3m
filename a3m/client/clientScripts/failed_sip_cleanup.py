#!/usr/bin/env python2
from __future__ import absolute_import

import argparse

import django
from django.db import transaction

django.setup()

from a3m.client import metrics


REJECTED = "reject"
FAILED = "fail"


def main(job, fail_type, sip_uuid):
    metrics.sip_failed(fail_type)

    return 0


def call(jobs):
    parser = argparse.ArgumentParser(description="Cleanup from failed/rejected SIPs.")
    parser.add_argument("fail_type", help='"%s" or "%s"' % (REJECTED, FAILED))
    parser.add_argument("sip_uuid", help="%SIPUUID%")

    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                args = parser.parse_args(job.args[1:])
                job.set_status(main(job, args.fail_type, args.sip_uuid))
