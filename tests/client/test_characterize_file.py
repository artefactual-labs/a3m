import pytest

from a3m.client.clientScripts.characterize_file import main
from a3m.client.job import Job
from a3m.main.models import SIP
from a3m.main.models import File
from a3m.main.models import FPCommandOutput


@pytest.mark.django_db
def test_characterization_runs_shell_command_with_file_path(
    tmp_path, monkeypatch, mocker
):
    sip = SIP.objects.create(currentpath=str(tmp_path))
    path = tmp_path / "file with spaces.flif"
    path.write_bytes(b"sample")
    file = File.objects.create(
        sip=sip, originallocation=str(path), currentlocation=str(path)
    )
    file.fileformatversion_set.create(
        format_version_id="3b66cb99-49a4-4374-88d4-06b0ecbce50e",  # fmt/872
    )

    ffprobe = tmp_path / "ffprobe"
    ffprobe.write_text(
        "#!/bin/sh\n"
        '[ "$1" = "-i" ] && [ "$2" = "$EXPECTED_INPUT" ] || exit 1\n'
        "printf '<ffprobe><format>FLIF</format></ffprobe>'\n"
    )
    ffprobe.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("EXPECTED_INPUT", str(path))

    result = main(mocker.Mock(spec=Job), str(path), str(file.uuid), str(sip.uuid))

    assert result == 0
    output = FPCommandOutput.objects.get(file=file)
    assert output.content == "<ffprobe><format>FLIF</format></ffprobe>"
