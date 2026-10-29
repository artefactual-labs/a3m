from pathlib import Path
from uuid import uuid4

import pytest

from a3m.client.clientScripts.a3m_store_aip import call
from a3m.client.job import Job


@pytest.fixture
def uploaded_objects(mocker, settings):
    settings.S3_ENABLED = True
    settings.S3_BUCKET = "aips"
    objects = {}

    def upload_file(filename, bucket, key):
        objects[bucket, key] = Path(filename).read_bytes()

    resource = mocker.patch("a3m.client.clientScripts.a3m_store_aip.boto3.resource")
    resource.return_value.meta.client.upload_file.side_effect = upload_file
    return objects


@pytest.mark.django_db
def test_store_aip_uploads_archive_from_job_arguments(tmp_path, uploaded_objects):
    archive = tmp_path / "package with spaces.7z"
    archive.write_bytes(b"A compressed preservation package")
    sip_id = str(uuid4())
    job = Job("a3m_store_aip", str(uuid4()), [sip_id, str(archive)])

    call([job])

    assert job.get_exit_code() == 0, job.get_stderr()
    assert uploaded_objects == {("aips", sip_id): archive.read_bytes()}


@pytest.mark.django_db
def test_store_aip_rejects_uncompressed_directory(tmp_path, uploaded_objects):
    job = Job("a3m_store_aip", str(uuid4()), [str(uuid4()), str(tmp_path)])

    call([job])

    assert job.get_exit_code() == 1
    assert "AIP must be compressed" in job.get_stderr()
    assert uploaded_objects == {}
