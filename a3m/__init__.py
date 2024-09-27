import os
import warnings
from importlib.metadata import version

__version__ = version("a3m")

__all__ = ["__version__"]


# Hide protobuf outdated warnings (see https://github.com/grpc/grpc/issues/37609).
warnings.filterwarnings(
    "ignore", ".*obsolete", UserWarning, "google.protobuf.runtime_version"
)

# Hide warning: Other threads are currently calling into gRPC, skipping fork() handlers.
# TODO: investigate root issue.
os.environ.setdefault("GRPC_ENABLE_FORK_SUPPORT", "false")
