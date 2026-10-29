import subprocess
import uuid
from pathlib import Path

import pytest

from a3m.api.transferservice.v1beta1.request_response_pb2 import ProcessingConfig
from a3m.client.clientScripts.compress_aip import compress_aip
from a3m.client.job import Job
from a3m.main.models import SIP
from a3m.main.models import Event


@pytest.mark.skipif(not Path("/usr/bin/7z").exists(), reason="Requires system 7z")
@pytest.mark.parametrize(
    "banner,expected",
    [
        (None, "7-Zip"),
        ("\n7-Zip [64] 16.02\np7zip Version 16.02\n", "p7zip Version 16.02"),
        ("\n7-Zip 25.01 (x64)\n 64-bit locale=en_US.UTF-8\n", "7-Zip 25.01 (x64)"),
    ],
)
@pytest.mark.django_db
def test_compression_records_7z_version(tmp_path, monkeypatch, banner, expected):
    sip = SIP.objects.create(uuid=str(uuid.uuid4()))
    package = tmp_path / f"sample-{sip.uuid}"
    package.mkdir()
    (package / "document.txt").write_text("Preserve this content.")
    if banner is not None:
        tools = tmp_path / "bin"
        tools.mkdir()
        executable = tools / "7z"
        executable.write_text("#!/bin/sh\ncat <<'BANNER'\n" + banner + "BANNER\n")
        executable.chmod(0o755)
        monkeypatch.setenv("PATH", str(tools), prepend=":")
    job = Job("compress_aip", str(uuid.uuid4()), [])

    status = compress_aip(
        job,
        ProcessingConfig.AIP_COMPRESSION_ALGORITHM_S7_COPY,
        "1",
        f"{tmp_path}/",
        "sample",
        sip.uuid,
    )

    assert status == 0, job.error
    sip.refresh_from_db()
    archive = tmp_path / sip.aip_filename
    subprocess.run(
        ["/usr/bin/7z", "t", str(archive)],
        check=True,
        capture_output=True,
    )
    event = Event.objects.get(file_uuid=sip.uuid, event_type="compression")
    assert "program=7z; algorithm=copy; version=" in event.event_detail
    assert expected in event.event_detail.split("version=", 1)[1]
