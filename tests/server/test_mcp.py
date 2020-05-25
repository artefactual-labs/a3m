import threading

from a3m.server.mcp import ExecutionMode
from a3m.server.mcp import main


def test_mcp_main(mocker, settings):
    """Test spin up with immediate shutdown.

    This test has limited utility because everything is mocked, but it should
    help catch basic errors.
    """
    # Don't bother starting many threads
    settings.RPC_THREADS = 1
    settings.WORKER_THREADS = 1
    settings.PROMETHEUS_ENABLED = True

    mock_load_default_workflow = mocker.patch("a3m.server.mcp.load_default_workflow")
    mock_shared_dirs = mocker.patch("a3m.server.mcp.shared_dirs")
    mock_job = mocker.patch("a3m.server.mcp.Job")
    mock_task = mocker.patch("a3m.server.mcp.Task")
    mock_db_migrate = mocker.patch("a3m.server.mcp.migrate")
    mock_metrics = mocker.patch("a3m.server.mcp.metrics")

    shutdown_event = threading.Event()
    shutdown_event.set()

    main(mode=ExecutionMode.RPC, shutdown_event=shutdown_event)

    mock_load_default_workflow.assert_called_once()
    mock_shared_dirs.create.assert_called_once()
    mock_job.cleanup_old_db_entries.assert_called_once()
    mock_task.cleanup_old_db_entries.assert_called_once()
    mock_db_migrate.assert_called_once()
    mock_metrics.start_prometheus_server.assert_called_once()
