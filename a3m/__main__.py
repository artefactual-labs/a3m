#!/usr/bin/env python2
import os
import sys


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "a3m.settings.common")

subcommand = None
try:
    subcommand = sys.argv[1]
except IndexError:
    sys.exit("Missing subcommand")

if subcommand == "server":
    from server.mcp import main

    main()
elif subcommand == "client":
    from client.mcp import main

    main()
else:
    sys.exit("Unknown command")
