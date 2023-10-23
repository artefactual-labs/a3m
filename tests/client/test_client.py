import pytest

from a3m.client.mcp import handle_batch_task


@pytest.mark.django_db
def test_handle_batch_task_replaces_non_ascii_arguments(mocker):
    # We are only interested in verifying the string replacement logic
    # for task arguments and mock the remaining functionality
    mocker.patch("a3m.client.mcp.Job")
    mocker.patch("a3m.client.mcp.Task")
    mocker.patch("a3m.client.mcp.retryOnFailure")

    # This is the only function that uses the arguments after the replacements
    _parse_command_line = mocker.patch("a3m.client.mcp._parse_command_line")

    # The mocked module will not have a `concurrent_instances` attribute
    mocker.patch(
        "importlib.import_module", return_value=mocker.MagicMock(spec=["call"])
    )

    # Mock the two parameters sent to handle_batch_task
    task_name = "tásk".encode()
    batch_payload = {
        "tasks": {
            "some_task_uuid": {
                "uuid": "some_task_uuid",
                "arguments": "montréal %taskUUID% %jobCreatedDate%",
                "createdDate": "some montréal datetime",
                "wants_output": False,
                "execute": "command",
            }
        }
    }
    handle_batch_task(task_name, batch_payload)

    # Check that string replacement were successful
    _parse_command_line.assert_called_once_with(
        "montréal some_task_uuid some montréal datetime"
    )
