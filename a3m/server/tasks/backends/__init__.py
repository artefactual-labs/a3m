"""
Handle offloading of Task objects to MCP Client for processing.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import threading

from a3m.server.tasks.backends.base import TaskBackend
from a3m.server.tasks.backends.gearman_backend import GearmanTaskBackend
from a3m.server.tasks.backends.pool_backend import PoolTaskBackend


# This could be a configuration setting.
DEFAULT_BACKEND = PoolTaskBackend

# When a backend needs to be thread-local so theads own an instance.
backend_local = threading.local()

# When a backend is shared across all threads.
backend_global = None


def get_task_backend():
    """Return the backend for processing tasks."""
    if DEFAULT_BACKEND == PoolTaskBackend:
        global backend_global
        if backend_global is None:
            backend_global = PoolTaskBackend()
        return backend_global

    if DEFAULT_BACKEND == GearmanTaskBackend:
        if not getattr(backend_local, "task_backend", None):
            backend_local.task_backend = GearmanTaskBackend()
        return backend_local.task_backend


__all__ = ("GearmanTaskBackend", "PoolTaskBackend", "TaskBackend", "get_task_backend")
