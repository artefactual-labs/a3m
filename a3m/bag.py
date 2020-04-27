import multiprocessing
import sys
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


def is_valid(path, completeness_only=False, printfn=print):
    """Return whether a BagIt package is valid given its ``path``."""
    try:
        bag = Bag(path)
        bag.validate(
            processes=multiprocessing.cpu_count(), completeness_only=completeness_only
        )
    except BagError as err:
        printfn("Error validating BagIt package:", err, file=sys.stderr)
        return False
    return True
