from a3m.client.clientScripts.copy_submission_docs import call
from a3m.client.job import Job


def test_absent_submission_documentation_is_optional(tmp_path):
    job = Job("copy_submission_docs", "test", [str(tmp_path), "package"])

    call([job])

    assert job.int_code == 0
    assert job.error == ""
    assert "No submission documentation" in job.output


def test_submission_documentation_is_copied(tmp_path):
    source = tmp_path / "package/data/objects/submissionDocumentation"
    source.mkdir(parents=True)
    (source / "deposit agreement.txt").write_text("Keep this document.")
    job = Job("copy_submission_docs", "test", [str(tmp_path), "package"])

    call([job])

    assert job.int_code == 0
    assert job.error == ""
    copied = (
        tmp_path
        / "submissionDocumentation/submissionDocumentation/deposit agreement.txt"
    )
    assert copied.read_text() == "Keep this document."


def test_submission_documentation_copy_failure_is_reported(tmp_path):
    source = tmp_path / "package/data/objects/submissionDocumentation"
    source.mkdir(parents=True)
    destination = tmp_path / "submissionDocumentation"
    destination.mkdir()
    (destination / "submissionDocumentation").write_text("Conflicting file")
    job = Job("copy_submission_docs", "test", [str(tmp_path), "package"])

    call([job])

    assert job.int_code != 0
    assert job.error
