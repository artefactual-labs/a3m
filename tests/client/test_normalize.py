import argparse
import hashlib
import json
import shutil
import subprocess
import uuid

import pytest

from a3m.client.clientScripts.normalize import main
from a3m.client.job import Job
from a3m.main.models import SIP
from a3m.main.models import Derivation
from a3m.main.models import Event
from a3m.main.models import File


@pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="JPEG 2000 normalization requires FFmpeg and FFprobe",
)
@pytest.mark.django_db
def test_normalize_jpeg2000_creates_preservation_tiff(tmp_path, mocker):
    objects = tmp_path / "objects"
    objects.mkdir()
    source = objects / "image with spaces.jp2"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=32x32",
            "-frames:v",
            "1",
            "-c:v",
            "jpeg2000",
            str(source),
        ],
        check=True,
    )
    sip = SIP.objects.create(uuid=str(uuid.uuid4()), currentpath=f"{tmp_path}/")
    location = f"%SIPDirectory%objects/{source.name}"
    original = File.objects.create(
        uuid=str(uuid.uuid4()),
        sip=sip,
        originallocation=location,
        currentlocation=location,
        filegrpuse="original",
    )
    original.fileformatversion_set.create(
        format_version_id="734edb99-968d-42fc-9fc6-342b86fcb6e6",  # x-fmt/392
    )
    task_uuid = str(uuid.uuid4())
    opts = argparse.Namespace(
        file_uuid=str(original.uuid),
        file_path=str(source),
        sip_path=f"{tmp_path}/",
        sip_uuid=str(sip.uuid),
        task_uuid=task_uuid,
        normalize_file_grp_use="original",
    )

    job = mocker.Mock(spec=Job)
    assert main(job, opts) == 0, job.write_error.call_args_list

    derivative = File.objects.get(uuid=task_uuid, filegrpuse="preservation")
    output = tmp_path / derivative.currentlocation.removeprefix("%SIPDirectory%")
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )
    stream = json.loads(result.stdout)["streams"][0]
    assert (stream["codec_name"], stream["width"], stream["height"]) == ("tiff", 32, 32)
    assert derivative.checksum == hashlib.sha256(output.read_bytes()).hexdigest()
    assert Event.objects.filter(
        file_uuid=original.uuid, event_type="normalization"
    ).exists()
    assert Derivation.objects.filter(
        source_file=original, derived_file=derivative
    ).exists()
