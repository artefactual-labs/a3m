from pathlib import Path

from bagit import Bag
from bagit import BagError


def is_bag(path):
    """Determine whether the directory contains a BagIt package.

    The constructor of ``Bag`` is fast enough but we may prefer to optimize
    later.
    """
    if isinstance(path, Path):
        path = str(path)
    try:
        Bag(path)
    except BagError:
        return False
    return True
