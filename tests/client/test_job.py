from uuid import uuid4

from a3m.client.job import Job


UNICODE = "‘你好‘"
NON_ASCII = "‘你好‘"


def test_job_encoding():
    job = Job(name="somejob", uuid=str(uuid4()), args=["a", "b"])

    job.pyprint(UNICODE)
    stdout = job.get_stdout()
    expected_stdout = f"{UNICODE}\n"
    expected_output = f"{UNICODE}\n"
    assert job.output == expected_output
    assert stdout == expected_stdout
    assert isinstance(job.output, str)
    assert isinstance(stdout, str)

    job.print_error(NON_ASCII)
    stderr = job.get_stderr()
    expected_stderr = f"{NON_ASCII}\n"
    expected_error = f"{NON_ASCII}\n"
    assert job.error == expected_error
    assert stderr == expected_stderr
    assert isinstance(job.error, str)
    assert isinstance(stderr, str)

    job_dump = job.dump()
    assert job.UUID in job_dump
    assert stderr in job_dump
    assert stdout in job_dump
