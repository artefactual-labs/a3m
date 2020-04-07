#!/usr/bin/env python2

import argparse

import requests

import django

django.setup()
from django.db import transaction

# dashboard
from main import models

from custom_handlers import get_script_logger
import storageService as storage_service

logger = get_script_logger("archivematica.mcp.client.post_store_aip_hook")

COMPLETED = 0
NO_ACTION = 1
ERROR = 2


def post_store_hook(job, sip_uuid):
    """
    Hook for doing any work after an AIP is stored successfully.
    """
    # SIP ARRANGEMENT

    # Mark files in this SIP as in an AIP (aip_created)
    file_uuids = models.File.objects.filter(sip=sip_uuid).values_list("uuid", flat=True)
    models.SIPArrange.objects.filter(file_uuid__in=file_uuids).update(aip_created=True)

    # Check if any of component transfers are completely stored
    # TODO Storage service should index AIPs, knows when to update ES
    transfer_uuids = set(
        models.SIPArrange.objects.filter(file_uuid__in=file_uuids).values_list(
            "transfer_uuid", flat=True
        )
    )
    for transfer_uuid in transfer_uuids:
        job.pyprint("Checking if transfer", transfer_uuid, "is fully stored...")
        arranged_uuids = set(
            models.SIPArrange.objects.filter(transfer_uuid=transfer_uuid)
            .filter(aip_created=True)
            .values_list("file_uuid", flat=True)
        )
        backlog_uuids = set(
            models.File.objects.filter(transfer=transfer_uuid).values_list(
                "uuid", flat=True
            )
        )
        # If all backlog UUIDs have been arranged
        if arranged_uuids == backlog_uuids:
            job.pyprint(
                "Transfer",
                transfer_uuid,
                "fully stored, sending delete request to storage service, deleting from transfer backlog",
            )
            # Submit delete req to SS (not actually delete), remove from ES
            storage_service.request_file_deletion(
                uuid=transfer_uuid,
                user_id=0,
                user_email="archivematica system",
                reason_for_deletion="All files in Transfer are now in AIPs.",
            )

    # POST-STORE CALLBACK
    storage_service.post_store_aip_callback(sip_uuid)


def call(jobs):
    parser = argparse.ArgumentParser()
    parser.add_argument("sip_uuid", help="%SIPUUID%")

    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                args = parser.parse_args(job.args[1:])
                job.set_status(post_store_hook(job, args.sip_uuid))
