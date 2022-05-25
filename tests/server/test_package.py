import concurrent.futures
import os
import threading
import uuid
from pathlib import Path

import pytest

from a3m.api.transferservice.v1beta1.request_response_pb2 import ProcessingConfig
from a3m.main import models
from a3m.server.packages import Package
from a3m.server.queues import PackageQueue
from a3m.server.workflow import load as load_workflow

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
INTEGRATION_TEST_PATH = os.path.join(FIXTURES_DIR, "workflow-integration-test.json")


@pytest.fixture
def workflow(request):
    with open(INTEGRATION_TEST_PATH) as workflow_file:
        return load_workflow(workflow_file)


@pytest.fixture
def package_queue(request):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    return PackageQueue(executor, threading.Event(), debug=True)


@pytest.fixture
def package(request, db, package_queue, workflow):
    return Package.create_package(
        package_queue,
        package_queue.executor,
        workflow,
        "name",
        "file:///tmp/foobar.gz",
        ProcessingConfig(),
    )


@pytest.mark.django_db(transaction=True)
def test_reload_file_list(tmp_path, package):
    path = tmp_path / f"test-transfer-{package.subid}"
    package.current_path = str(path)

    # Add files to the transfer to simulate a transfer existing on disk.
    path.mkdir()
    objects_path = path / "objects"
    objects_path.mkdir()
    first_file = objects_path / "file.txt"
    first_file.touch()

    kwargs = {
        "uuid": uuid.uuid4(),
        "currentlocation": "".join(
            [package.replacement_path_string, str(Path("/objects/file.txt"))]
        ),
        "filegrpuse": "original",
        "transfer_id": package.subid,
    }
    models.File.objects.create(**kwargs)
    assert models.File.objects.filter(transfer_id=str(package.subid)).count() == 1

    # Add a new file to the file-system, e.g. to simulate normalization for
    # preservation adding a new object.
    new_file = objects_path / "new_file.txt"
    new_file.touch()

    # One file will be returned from the database  with a UUID, another from
    # the filesystem without a UUID.
    for file_count, file_info in enumerate(package.files("/objects"), 1):
        assert "%fileUUID%" in file_info
        assert "%fileGrpUse%" in file_info
        assert "%relativeLocation%" in file_info
        if file_info.get("%fileUUID%") != "None":
            continue
        assert file_info.get("%relativeLocation%") == str(new_file)
        file_path = "".join(
            [
                package.replacement_path_string,
                "/objects",
                file_info.get("%relativeLocation%").split("objects")[1],
            ]
        )
        kwargs = {
            "uuid": uuid.uuid4(),
            "currentlocation": file_path,
            "filegrpuse": "original",
            "transfer_id": package.subid,
        }
        models.File.objects.create(**kwargs)
    assert (
        file_count == 2
    ), "Database and file objects were not returned by the generator"
    assert models.File.objects.filter(transfer_id=str(package.subid)).count() == 2

    # Simulate an additional file object being added later on in the transfer
    # in a sub directory of the objects folder, e.g. transcribe contents.
    sub_dir = objects_path / "subdir"
    sub_dir.mkdir()
    new_file = sub_dir / "another_new_file.txt"
    new_file.touch()
    for file_count, file_info in enumerate(package.files("/objects"), 1):
        file_path = "".join(
            [
                package.replacement_path_string,
                "/objects",
                file_info.get("%relativeLocation%").split("objects")[1],
            ]
        )
        if file_info.get("%fileUUID%") != "None":
            continue
        kwargs = {
            "uuid": uuid.uuid4(),
            "currentlocation": file_path,
            "filegrpuse": "original",
            "transfer_id": package.subid,
        }
        models.File.objects.create(**kwargs)
    assert (
        file_count == 3
    ), "Database and file objects were not returned by the generator"
    assert models.File.objects.filter(transfer_id=str(package.subid)).count() == 3

    # Now the database is updated, we will still have the same file count, but
    # all objects will be returned from the database and we will have uuids.
    for file_count, file_info in enumerate(package.files("/objects"), 1):
        if file_info.get("%fileUUID%") == "None":
            assert (
                False
            ), "Non-database entries returned from package.files(): {}".format(
                file_info
            )
    assert file_count == 3

    # Finally, let's just see if the scan works for a slightly larger no.
    # files, i.e. a number with an increment slightly larger than one.
    files = ["f1", "f2", "f3", "f4", "f5"]
    for file_ in files:
        new_file = objects_path / file_
        new_file.touch()
    new_count = 0
    for file_count, file_info in enumerate(package.files("/objects"), 1):
        if file_info.get("%fileUUID%") == "None":
            new_count += 1
    assert new_count == 5
    assert file_count == 8

    # Clean up state and ensure test doesn't interfere with other transfers
    # expected to be in the database, e.g. in test_queues.py.
    models.File.objects.filter(transfer_id=str(package.subid)).delete()


@pytest.mark.django_db(transaction=True)
def test_package_files_with_non_ascii_names(tmp_path, package):
    path = tmp_path / f"test-transfer-{package.subid}"
    package.current_path = str(path)

    # Add a file to the transfer with non-ascii name
    path.mkdir()
    objects = path / "objects"
    objects.mkdir()
    file_ = objects / "montréal.txt"
    file_.touch()

    # Create a File model instance for the transfer file
    kwargs = {
        "uuid": uuid.uuid4(),
        "currentlocation": "".join(
            [package.replacement_path_string, "/objects/montréal.txt"]
        ),
        "filegrpuse": "original",
        "transfer_id": package.subid,
    }
    models.File.objects.create(**kwargs)

    # Assert only one file is returned
    result = list(package.files("/objects"))
    assert len(result) == 1

    # And it is the file we just created
    assert result[0]["%fileUUID%"] == str(kwargs["uuid"])
    assert result[0]["%currentLocation%"] == kwargs["currentlocation"]
    assert result[0]["%fileGrpUse%"] == kwargs["filegrpuse"]
