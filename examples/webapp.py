#!/usr/bin/env python
"""HTTP gateway for a3m.

When executed, this module starts a simple HTTP server that submits transfers
to an embedded a3m server instance on every GET request received.

Usage::

    $ pip install a3m
    $ ./webapp.py
    $ curl 127.0.0.1:33892

"""
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from threading import Thread

import grpc

from a3m.cli.common import init_django

init_django()  # This will not be needed in the future.
from a3m.server.runner import create_server
from a3m.server.rpc.client import Client


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args):
        super().__init__(*args)

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        try:
            resp = a3mc.submit(
                name="Test",
                url="https://github.com/artefactual/archivematica-sampledata/raw/master/SampleTransfers/ZippedDirectoryTransfers/DemoTransferCSV.zip",
            )
        except Exception as err:
            self.wfile.write(f"Error: {err}".encode())
        else:
            self.wfile.write(f"Transfer submitted! {resp.id}".encode())


a3md = create_server(
    bind_address="127.0.0.1:0",
    server_credentials=grpc.local_server_credentials(
        grpc.LocalConnectionType.LOCAL_TCP
    ),
    max_concurrent_packages=1,
    batch_size=125,
    queue_workers=3,
    grpc_workers=3,
)
a3md_thread = Thread(target=a3md.start)
a3md_thread.start()

httpd = ThreadingHTTPServer(("127.0.0.1", 0), RequestHandler)
httpd_thread = Thread(target=httpd.serve_forever)
httpd_thread.start()
print(f"Web server listening on port {httpd.server_port}/tcp.")

a3mc = Client(grpc.insecure_channel(f"127.0.0.1:{a3md.grpc_port}"))

a3md_thread.join()
