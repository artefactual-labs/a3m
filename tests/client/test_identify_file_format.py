import uuid

import pytest

from a3m.client.clientScripts.identify_file_format import main
from a3m.main.models import Event
from a3m.main.models import File
from a3m.main.models import FileID
from a3m.main.models import Transfer


@pytest.fixture()
def subdir_path(tmp_path):
    subdir = tmp_path / "subdir1"
    subdir.mkdir()

    return subdir


@pytest.fixture()
def file_path(subdir_path):
    file_path = subdir_path / "script.py"
    file_path.write_text("import sys; sys.exit(0)")

    return file_path


@pytest.fixture()
def transfer(db):
    return Transfer.objects.create(
        uuid=uuid.uuid4(), currentlocation=r"%transferDirectory%"
    )


@pytest.fixture()
def file_obj(db, transfer, tmp_path, file_path):
    file_obj_path = "".join(
        [transfer.currentlocation, str(file_path.relative_to(tmp_path))]
    )
    file_obj = File.objects.create(
        uuid=uuid.uuid4(),
        transfer=transfer,
        originallocation=file_obj_path,
        currentlocation=file_obj_path,
        removedtime=None,
        size=24,
        checksum="7e272e3e7076fef4248bc278918ecf003f05f275dff3bdb9140f1f4120b76ff1",
        checksumtype="sha256",
    )

    return file_obj


def test_identify_file_format(file_obj, file_path):
    code = main(str(file_path), file_obj.uuid, disable_reidentify=False)
    assert code == 0

    format_version = file_obj.get_format_version()
    assert format_version is not None
    assert format_version.pronom_id == "fmt/938"

    Event.objects.get(
        file_uuid=file_obj,
        event_type="format identification",
        event_outcome="Positive",
        event_outcome_detail="fmt/938",
    )
    FileID.objects.get(
        file_id=file_obj.uuid,
        format_name="Python Script File",
        format_registry_key="fmt/938",
    )
