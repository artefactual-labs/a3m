import pytest

from a3m.client.clientScripts.validate_file import main
from a3m.client.job import Job
from a3m.main.models import Event
from a3m.main.models import File
from a3m.main.models import FileFormatVersion
from a3m.main.models import SIP


@pytest.fixture
def sip(tmp_path):
    sip_dir = tmp_path / "sip"
    sip_dir.mkdir()
    # Create logs directory in the SIP.
    (sip_dir / "logs").mkdir()

    return SIP.objects.create(currentpath=str(sip_dir))


@pytest.fixture
def file_obj(tmp_path, sip):
    d = tmp_path / "dir"
    d.mkdir()
    txt_file = d / "file.txt"
    txt_file.write_text("hello world")

    f = File.objects.create(
        sip=sip, originallocation=txt_file, currentlocation=txt_file
    )
    f.fileformatversion_set.create(
        # Known format version with validation rule.
        format_version_id="45928c95-1fea-4b2b-af54-9aa3807e26a2",
    )

    return f


@pytest.fixture
def file_format_version(file_obj, format_version):
    FileFormatVersion.objects.create(file_uuid=file_obj, format_version=format_version)


@pytest.mark.django_db
def test_main(mocker, sip, file_obj):
    exit_status = 0
    stdout = '{"eventOutcomeInformation": "pass", "eventOutcomeDetailNote": "a note"}'
    stderr = ""
    execute_or_run = mocker.patch(
        "a3m.client.clientScripts.validate_file.executeOrRun",
        return_value=(exit_status, stdout, stderr),
    )
    job = mocker.Mock(spec=Job)
    file_type = "original"

    main(
        job=job,
        file_path=file_obj.currentlocation,
        file_uuid=file_obj.uuid,
        sip_uuid=sip.uuid,
        shared_path=sip.currentpath,
        file_type=file_type,
    )

    # Check the executed script.
    called_args = execute_or_run.call_args
    assert called_args.kwargs["type"] == "pythonScript"
    assert called_args.kwargs["printing"] is False
    assert called_args.kwargs["arguments"] == [file_obj.currentlocation]

    # Verify a PREMIS validation event was created with the output of the
    # validation command.
    assert (
        Event.objects.filter(
            file_uuid=file_obj.uuid,
            event_type="validation",
            event_outcome="pass",
            event_outcome_detail="a note",
        ).count()
        == 1
    )
