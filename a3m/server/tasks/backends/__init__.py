"""
Handle offloading of Task objects to MCP Client for processing.
"""
from a3m.server.tasks.backends.base import TaskBackend
from a3m.server.tasks.backends.pool_backend import PoolTaskBackend


# This could be a configuration setting.
DEFAULT_BACKEND = PoolTaskBackend

# Backend is shared across all threads.
backend_global = None


def get_task_backend():
    """Return the backend for processing tasks."""
    if DEFAULT_BACKEND == PoolTaskBackend:
        global backend_global
        if backend_global is None:
            backend_global = PoolTaskBackend()
        return backend_global

    raise RuntimeError("Unsupported task backend")


__all__ = ("PoolTaskBackend", "TaskBackend", "get_task_backend")
