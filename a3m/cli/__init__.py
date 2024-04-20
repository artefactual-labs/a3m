import sys
from importlib.metadata import version


def shim_pkg_resources():
    """Injects a pkg_resources fake needed by bagit-python in Python 3.12.

    The underlying error is only reproducible if setuptools is not installed.
    """

    class Distribution:
        def __init__(self, name):
            self.version = version(name)

    class FakeDistributionNotFound(Exception):
        pass

    def fake_get_distribution(_, name):
        return Distribution(name)

    class PkgResources:
        DistributionNotFound = FakeDistributionNotFound
        get_distribution = fake_get_distribution

    sys.modules["pkg_resources"] = PkgResources()  # type: ignore


shim_pkg_resources()
