from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pytest

from a3m.server.jobs import Job
from a3m.server.tasks import PoolTaskBackend
from a3m.server.tasks import Task


class MockJob(Job):
    def __init__(self, *args, **kwargs):
        self.name = kwargs.pop("name", "")
        super(MockJob, self).__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        pass


@pytest.fixture
def simple_job(request, mocker):
    return MockJob(mocker.Mock(), mocker.Mock(), mocker.Mock(), name="test_v0.0")


@pytest.mark.django_db(transaction=True)
def test_pool(simple_job, settings, mocker):
    backend = PoolTaskBackend()
    backend.TASK_BATCH_SIZE = 1

    for item in range(3):
        backend.submit_task(
            simple_job,
            Task(
                "/etc/fstab",
                "/dev/null",
                "/dev/null",
                {r"%relativeLocation%": "testfile"},
                wants_output=False,
            ),
        )

    results = list(backend.wait_for_results(simple_job))

    assert len(results) == 3
    assert results[0].done is True
    assert results[1].done is True
    assert results[2].done is True
