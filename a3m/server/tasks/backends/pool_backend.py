"""
Built-in task backend. Submits `Task` objects to a local pool of processes for
processing, and returns results.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


class PoolTaskBackend(TaskBackend):
    """Submits tasks to the pool.

    Tasks are batched into BATCH_SIZE groups (default 128), pickled and sent to
    MCPClient. This adds some complexity but saves a lot of overhead.
    """
