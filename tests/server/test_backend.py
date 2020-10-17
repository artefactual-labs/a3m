import pytest

from a3m.server.jobs import Job
from a3m.server.tasks import get_task_backend
from a3m.server.tasks import Task
from a3m.server.tasks import TaskBackend


class MockJob(Job):
    def __init__(self, *args, **kwargs):
        self.name = kwargs.pop("name", "")
        super().__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        pass


@pytest.fixture
def simple_job(request, mocker):
    return MockJob(mocker.Mock(), mocker.Mock(), mocker.Mock(), name="test_v0.0")


@pytest.fixture
def simple_task(request):
    return Task(
        "command",
        "a argument string",
        "/dev/stdoutfile",
        "/tmp/stderrfile",
        {r"%relativeLocation%": "testfile"},
        wants_output=False,
    )


def format_result(task_results):
    """Accepts task results as a tuple of (uuid, result_dict)."""
    response = {"task_results": {}}
    for task_uuid, task_data in task_results:
        task_uuid = str(task_uuid)
        response["task_results"][task_uuid] = task_data

    return response


# test_gearman_task_submission
# test_gearman_task_result_success
# test_gearman_task_result_error


def test_multiple_batches(simple_job, simple_task, mocker):
    mocker.patch("a3m.server.tasks.backends.pool_backend.Task.bulk_log")
    mocker.patch("a3m.server.tasks.backends.pool_backend.Task.write_output")
    mocker.patch("a3m.server.tasks.backends.pool_backend.init_counter_labels")
    mocker.patch.object(TaskBackend, "TASK_BATCH_SIZE", 2)

    def execute_command(task_name: str, batch_payload):
        assert task_name == "test_v0.0"
        return {
            "task_results": {
                task_id: {
                    "exitCode": 0,
                    "stdout": "stdout example",
                    "stderr": "stderr example",
                }
                for task_id, task in batch_payload["tasks"].items()
            }
        }

    execute_command = mocker.patch(
        "a3m.server.tasks.backends.pool_backend.execute_command",
        side_effect=execute_command,
    )

    backend = get_task_backend()

    for item in range(3):
        backend.submit_task(simple_job, simple_task)

    results = list(backend.wait_for_results(simple_job))
    assert execute_command.call_count == 2
    assert len(results) == 3
    assert results[0].done is True
    assert results[0].exit_code == 0
    assert results[1].done is True
    assert results[1].exit_code == 0
    assert results[2].done is True
    assert results[2].exit_code == 0
