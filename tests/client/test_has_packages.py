from pathlib import Path
from uuid import uuid4

import pytest

from a3m.client.clientScripts import has_packages
from a3m.client.job import Job
from a3m.main.models import File
from a3m.main.models import Transfer


@pytest.fixture
def transfer(db, tmp_path):
    transfer_dir = tmp_path / "transfer"
    transfer_dir.mkdir()

    return Transfer.objects.create(currentlocation=str(transfer_dir))


@pytest.fixture
def compressed_file(db, transfer):
    # Simulate a compressed file being extracted to a directory with the same name.
    d = Path(transfer.currentlocation) / "compressed.zip"
    d.mkdir()

    # Place an extracted file in it.
    f = d / "file.txt"
    f.touch()

    # Create File models for the compressed and extracted files.
    result = File.objects.create(
        uuid=uuid4(), transfer=transfer, originallocation=d, currentlocation=d
    )
    File.objects.create(
        uuid=uuid4(), transfer=transfer, originallocation=f, currentlocation=f
    )

    # Create a file format version for the compressed file.
    # ce097bf8 is a fpr.formatversion for 7zip with an extraction rule.
    result.fileformatversion_set.create(
        format_version_id="ce097bf8-dc4d-4083-932e-82224890f26a"
    )

    return result


def test_main_detects_file_is_extractable_via_fpr(
    db, mocker, transfer, compressed_file
):
    job = mocker.Mock(spec=Job)

    result = has_packages.main(job, str(transfer.uuid))

    assert result == 0


def test_main_detects_file_was_already_extracted_from_unpacking_event(
    db, mocker, transfer, compressed_file
):
    job = mocker.Mock(spec=Job)

    extracted_file = File.objects.get(
        currentlocation__startswith=compressed_file.currentlocation,
        currentlocation__endswith="file.txt",
    )
    extracted_file.event_set.create(
        event_type="unpacking",
        event_detail=f"Unpacked from: {extracted_file.currentlocation} ({compressed_file.uuid})",
    )

    result = has_packages.main(job, str(transfer.uuid))

    assert result == 1
