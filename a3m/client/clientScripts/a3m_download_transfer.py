"""Download transfer object from storage."""
import os
import shutil
from tempfile import mkdtemp

import requests
from django.conf import settings
from django.db import transaction

from a3m.bag import is_bag
from a3m.client.clientScripts.extract_zipped_transfer import extract
from a3m.main.models import Transfer
from a3m.main.models import UnitVariable


def _create_tmpdir(suffix):
    suffix = f".{suffix}"
    return mkdtemp(suffix=suffix, dir=settings.TEMP_DIRECTORY)


def _download_object(url, filename):
    with requests.get(url, allow_redirects=True, stream=True) as resp:
        resp.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def main(job, transfer_id, url):
    tmp_dir = _create_tmpdir(transfer_id)
    object_file = os.path.join(tmp_dir, "object")
    contents_dir = os.path.join(tmp_dir, "contents")
    processing_dir = os.path.join(settings.PROCESSING_DIRECTORY, transfer_id)

    if os.path.exists(processing_dir):
        raise Exception("Transfer already in processing directory")

    # Download object.
    _download_object(url, object_file)

    # Extract contents.
    exit_code = extract(job, object_file, contents_dir)
    if exit_code != 0:
        raise Exception("Extraction failed")

    # Determine whether it is a bag.
    bagged = is_bag(contents_dir)

    # Move to processing directory.
    shutil.move(contents_dir, processing_dir)
    with transaction.atomic():
        transfer = Transfer.objects.select_for_update().filter(pk=transfer_id).first()
        transfer.currentlocation = processing_dir
        transfer.save()

    if bagged:
        next_link_id = "154dd501-a344-45a9-97e3-b30093da35f5"
    else:
        next_link_id = "045c43ae-d6cf-44f7-97d6-c8a602748565"

    UnitVariable.objects.update_variable(
        "Transfer", transfer_id, "startingLinkID", value=None, link_id=next_link_id
    )

    shutil.rmtree(tmp_dir)


def call(jobs):
    job = jobs[0]
    transfer_id = job.args[1]
    url = job.args[2]
    job.pyprint(job.args[2])
    main(job, transfer_id, url)
