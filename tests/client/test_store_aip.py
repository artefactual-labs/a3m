from io import BytesIO
from pathlib import Path
from urllib.parse import parse_qs
from urllib.parse import urlsplit
from uuid import uuid4

import boto3
import pytest
from botocore.awsrequest import AWSResponse
from urllib3.response import HTTPResponse

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


@pytest.mark.django_db
@pytest.mark.parametrize("size", [7, 8 * 1024 * 1024 + 1])
def test_store_aip_https_uploads_without_checksum_trailers(
    monkeypatch, settings, tmp_path, size
):
    monkeypatch.delenv("AWS_REQUEST_CHECKSUM_CALCULATION", raising=False)
    requests = capture_s3_uploads(monkeypatch, settings)
    archive = tmp_path / "package.7z"
    archive.write_bytes(b"a" * size)
    sip_id = str(uuid4())
    job = Job("a3m_store_aip", str(uuid4()), [sip_id, str(archive)])

    call([job])

    assert job.get_exit_code() == 0, job.get_stderr()
    uploads = [
        item for item in requests if item["operation"] in {"PutObject", "UploadPart"}
    ]
    assert len(uploads) == (1 if size < 8 * 1024 * 1024 else 2)
    for item in uploads:
        assert urlsplit(item["url"]).path == f"/aips/{sip_id}"
        assert int(item["headers"]["content-length"]) == len(item["body"])
        assert "content-encoding" not in item["headers"]
        assert "transfer-encoding" not in item["headers"]
        assert "x-amz-trailer" not in item["headers"]
    uploads.sort(
        key=lambda item: int(
            parse_qs(urlsplit(item["url"]).query).get("partNumber", ["1"])[0]
        )
    )
    assert b"".join(item["body"] for item in uploads) == archive.read_bytes()


@pytest.mark.django_db
def test_store_aip_can_opt_in_to_https_checksum_trailers(
    monkeypatch, settings, tmp_path
):
    monkeypatch.setenv("AWS_REQUEST_CHECKSUM_CALCULATION", "when_supported")
    requests = capture_s3_uploads(monkeypatch, settings)
    archive = tmp_path / "package.7z"
    archive.write_bytes(b"A compressed preservation package")
    job = Job("a3m_store_aip", str(uuid4()), [str(uuid4()), str(archive)])

    call([job])

    assert job.get_exit_code() == 0, job.get_stderr()
    assert len(requests) == 1
    assert requests[0]["headers"]["content-encoding"] == "aws-chunked"
    assert requests[0]["headers"]["x-amz-trailer"] == "x-amz-checksum-crc32"


def capture_s3_uploads(monkeypatch, settings):
    settings.S3_ENABLED = True
    settings.S3_BUCKET = "aips"
    settings.S3_ENDPOINT_URL = "https://storage.example.invalid"
    settings.S3_REGION_NAME = "us-east-1"
    settings.S3_ACCESS_KEY_ID = "test"
    settings.S3_SECRET_ACCESS_KEY = "test-secret"
    settings.S3_ADDRESSING_STYLE = "path"
    settings.S3_USE_SSL = True
    session = boto3.Session()
    monkeypatch.setattr(boto3, "DEFAULT_SESSION", session)
    requests = []

    def respond(request, event_name, **kwargs):
        operation = event_name.rsplit(".", 1)[1]
        requests.append(
            {
                "operation": operation,
                "url": request.url,
                "headers": {
                    key.lower(): value.decode()
                    if isinstance(value, bytes)
                    else str(value)
                    for key, value in request.headers.items()
                },
                "body": request.body.read()
                if hasattr(request.body, "read")
                else request.body,
            }
        )
        if operation == "CreateMultipartUpload":
            body = b"<InitiateMultipartUploadResult><UploadId>upload</UploadId></InitiateMultipartUploadResult>"
        elif operation == "CompleteMultipartUpload":
            body = b'<CompleteMultipartUploadResult><ETag>"aip"</ETag></CompleteMultipartUploadResult>'
        else:
            assert operation in {"PutObject", "UploadPart"}
            body = b""
        return AWSResponse(
            request.url,
            200,
            {"ETag": '"part"'},
            HTTPResponse(body=BytesIO(body), preload_content=False),
        )

    # Replace only the HTTP transport: boto3 still opens the archive, selects
    # single or multipart upload, serializes it, and signs each request.
    session.events.register("before-send.s3", respond)
    return requests
