import uuid
from pathlib import Path

import pytest

from a3m.main import models
from a3m.server.packages import SIP
from a3m.server.packages import Transfer


@pytest.mark.django_db(transaction=True)
def test_transfer_get_or_create_from_db_path_without_uuid(tmp_path):
    transfer_path = tmp_path / "test-transfer"

    assert not models.Transfer.objects.filter(
        currentlocation=str(transfer_path)
    ).count()

    transfer = Transfer.get_or_create_from_db_by_path(str(transfer_path))

    assert transfer.current_path == str(transfer_path)
    try:
        models.Transfer.objects.get(currentlocation=str(transfer_path))
    except models.Transfer.DoesNotExist:
        pytest.fail(
            "Transfer.get_or_create_from_db_by_path didn't create a Transfer model"
        )


@pytest.mark.django_db(transaction=True)
def test_transfer_get_or_create_from_db_path_with_uuid(tmp_path):
    transfer_uuid = uuid.uuid4()
    transfer_path = tmp_path / f"test-transfer-{transfer_uuid}"

    transfer = Transfer.get_or_create_from_db_by_path(str(transfer_path))

    assert transfer.uuid == transfer_uuid
    assert transfer.current_path == str(transfer_path)
    try:
        models.Transfer.objects.get(uuid=transfer_uuid)
    except models.Transfer.DoesNotExist:
        pytest.fail(
            "Transfer.get_or_create_from_db_by_path didn't create a Transfer model"
        )


@pytest.mark.parametrize(
    "package_class, model, loc_attribute",
    [(Transfer, models.Transfer, "currentlocation"), (SIP, models.SIP, "currentpath")],
)
@pytest.mark.django_db(transaction=True)
def test_package_get_or_create_from_db_by_path_updates_model(
    tmp_path, settings, package_class, model, loc_attribute
):
    settings.SHARED_DIRECTORY = "custom-shared-path"
    package_id = uuid.uuid4()
    path_src = tmp_path / r"%sharedPath%" / "src" / f"test-transfer-{package_id}"
    path_dst = tmp_path / r"%sharedPath%" / "dst" / f"test-transfer-{package_id}"

    package_obj_src = package_class.get_or_create_from_db_by_path(str(path_src))
    package_obj_dst = package_class.get_or_create_from_db_by_path(str(path_dst))

    assert package_id == package_obj_src.uuid == package_obj_dst.uuid
    assert package_obj_src.current_path == str(path_src).replace(
        r"%sharedPath%", settings.SHARED_DIRECTORY
    )
    assert package_obj_dst.current_path == str(path_dst).replace(
        r"%sharedPath%", settings.SHARED_DIRECTORY
    )
    try:
        model.objects.get(**{"uuid": package_id, loc_attribute: path_dst})
    except models.Transfer.DoesNotExist:
        pytest.fail(
            "Method {}.get_or_create_from_db_by_path didn't update {} model".format(
                package_class.__name__, model.__name__
            )
        )


@pytest.mark.django_db(transaction=True)
def test_reload_file_list(tmp_path):

    # Create a transfer that will be updated through time to simulate
    # Archivematica's processing.
    transfer_uuid = uuid.uuid4()
    transfer_path = tmp_path / f"test-transfer-{transfer_uuid}"
    transfer = Transfer.get_or_create_from_db_by_path(str(transfer_path))

    # Add files to the transfer to simulate a transfer existing on disk.
    transfer_path.mkdir()
    objects_path = transfer_path / "objects"
    objects_path.mkdir()
    first_file = objects_path / "file.txt"
    first_file.touch()

    kwargs = {
        "uuid": uuid.uuid4(),
        "currentlocation": "".join(
            [transfer.REPLACEMENT_PATH_STRING, str(Path("/objects/file.txt"))]
        ),
        "filegrpuse": "original",
        "transfer_id": transfer_uuid,
    }
    models.File.objects.create(**kwargs)
    assert models.File.objects.filter(transfer_id=str(transfer_uuid)).count() == 1

    # Add a new file to the file-system, e.g. to simulate normalization for
    # preservation adding a new object.
    new_file = objects_path / "new_file.txt"
    new_file.touch()

    # One file will be returned from the database  with a UUID, another from
    # the filesystem without a UUID.
    for file_count, file_info in enumerate(transfer.files(None, None, "/objects"), 1):
        assert "%fileUUID%" in file_info
        assert "%fileGrpUse%" in file_info
        assert "%relativeLocation%" in file_info
        if file_info.get("%fileUUID%") != "None":
            continue
        assert file_info.get("%relativeLocation%") == str(new_file)
        file_path = "".join(
            [
                transfer.REPLACEMENT_PATH_STRING,
                "/objects",
                file_info.get("%relativeLocation%").split("objects")[1],
            ]
        )
        kwargs = {
            "uuid": uuid.uuid4(),
            "currentlocation": file_path,
            "filegrpuse": "original",
            "transfer_id": transfer_uuid,
        }
        models.File.objects.create(**kwargs)
    assert (
        file_count == 2
    ), "Database and file objects were not returned by the generator"
    assert models.File.objects.filter(transfer_id=str(transfer_uuid)).count() == 2

    # Simulate an additional file object being added later on in the transfer
    # in a sub directory of the objects folder, e.g. transcribe contents.
    sub_dir = objects_path / "subdir"
    sub_dir.mkdir()
    new_file = sub_dir / "another_new_file.txt"
    new_file.touch()
    for file_count, file_info in enumerate(transfer.files(None, None, "/objects"), 1):
        file_path = "".join(
            [
                transfer.REPLACEMENT_PATH_STRING,
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
            "transfer_id": transfer_uuid,
        }
        models.File.objects.create(**kwargs)
    assert (
        file_count == 3
    ), "Database and file objects were not returned by the generator"
    assert models.File.objects.filter(transfer_id=str(transfer_uuid)).count() == 3

    # Now the database is updated, we will still have the same file count, but
    # all objects will be returned from the database and we will have uuids.
    for file_count, file_info in enumerate(transfer.files(None, None, "/objects"), 1):
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
    for file_count, file_info in enumerate(transfer.files(None, None, "/objects"), 1):
        if file_info.get("%fileUUID%") == "None":
            new_count += 1
    assert new_count == 5
    assert file_count == 8

    # Clean up state and ensure test doesn't interfere with other transfers
    # expected to be in the database, e.g. in test_queues.py.
    models.File.objects.filter(transfer_id=str(transfer_uuid)).delete()


@pytest.mark.django_db(transaction=True)
def test_package_files_with_non_ascii_names(tmp_path):

    # Create a Transfer package
    transfer_uuid = uuid.uuid4()
    transfer_path = tmp_path / f"test-transfer-{transfer_uuid}"
    transfer = Transfer.get_or_create_from_db_by_path(str(transfer_path))

    # Add a file to the transfer with non-ascii name
    transfer_path.mkdir()
    objects = transfer_path / "objects"
    objects.mkdir()
    file_ = objects / "montréal.txt"
    file_.touch()

    # Create a File model instance for the transfer file
    kwargs = {
        "uuid": uuid.uuid4(),
        "currentlocation": "".join(
            [transfer.REPLACEMENT_PATH_STRING, "/objects/montréal.txt"]
        ),
        "filegrpuse": "original",
        "transfer_id": transfer_uuid,
    }
    models.File.objects.create(**kwargs)

    # Assert only one file is returned
    result = list(transfer.files(None, None, "/objects"))
    assert len(result) == 1

    # And it is the file we just created
    assert result[0]["%fileUUID%"] == str(kwargs["uuid"])
    assert result[0]["%currentLocation%"] == kwargs["currentlocation"]
    assert result[0]["%fileGrpUse%"] == kwargs["filegrpuse"]
