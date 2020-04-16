# -*- coding: utf-8 -*-
"""
Utility functions.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import uuid


def uuid_from_path(path):
    uuid_in_path = path.rstrip("/")[-36:]
    try:
        return uuid.UUID(uuid_in_path)
    except ValueError:
        return None
