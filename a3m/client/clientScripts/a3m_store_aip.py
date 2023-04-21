import logging
import sys

import boto3
from botocore.client import Config
from django.conf import settings
from django.db import transaction

from a3m.client import metrics

from pathlib import Path

logger = logging.getLogger(__name__)


def _upload_file(path, bucket, key):
    boto_args = {"service_name": "s3"}
    if settings.S3_ENDPOINT_URL:
        boto_args.update(endpoint_url=settings.S3_ENDPOINT_URL)
    if settings.S3_REGION_NAME:
        boto_args.update(region_name=settings.S3_REGION_NAME)
    if settings.S3_ACCESS_KEY_ID and settings.S3_SECRET_ACCESS_KEY:
        boto_args.update(
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        )
    if settings.S3_USE_SSL:
        boto_args.update(use_ssl=settings.S3_USE_SSL)

    s3_config = {}
    if settings.S3_ADDRESSING_STYLE:
        s3_config.update(addressing_style=settings.S3_ADDRESSING_STYLE)
    if settings.S3_SIGNATURE_VERSION:
        s3_config.update(signature_version=settings.S3_SIGNATURE_VERSION)
    if s3_config:
        config = Config(s3=s3_config)
        boto_args.update(config=config)

    s3 = boto3.resource(**boto_args)
    
    # TODO: The S3 path should include a pre-defined directory path for the AIP
    # We could use a predefined variable in the configuration file for a global A3M Storage such as predefined/global/path/<Transfer Source/DIPS/AIPS>/
    # Alternatively, we could use a predefined variable specifically for the AIP location such as predefined/aip/location/
    # In any case, the S3 path must be structured in a way that makes it easy to locate and manage the AIP.
    s3_path = key + path.suffix
    s3.meta.client.upload_file(str(path), bucket, s3_path)


def _store_aip(job, sip_id, aip_path):
    metrics.aip_stored(sip_id, size=0)  #  A3M-TODO: write size

    if not settings.S3_ENABLED:
        return

    # We're assuming that we don't have a directory!
    if aip_path.is_dir():
        job.pyprint("AIP must be compressed", file=sys.stderr)
        raise Exception("AIP is a directory")

    logger.info("Uploading AIP...")
    _upload_file(aip_path, settings.S3_BUCKET, sip_id)


def call(jobs):
    job = jobs[0]
    with transaction.atomic():
        with job.JobContext():
            sip_id = job.args[1]
            aip_path = Path(job.args[2])
            job.set_status(_store_aip(job, sip_id, aip_path))
