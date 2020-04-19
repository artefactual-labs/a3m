#!/usr/bin/env python2
from __future__ import absolute_import

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "a3m.settings.common")


from a3m.server.mcp import main

main()
