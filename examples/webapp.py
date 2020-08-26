"""Work in progres!"""
import sys
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from threading import Thread

import grpc

sys.path.append("/home/jesus/Projects/a3m")
from a3m.cli.common import init_django

init_django()  # This will not be needed in the future.
from a3m.server.runner import create_server


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args):
        super().__init__(*args)

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"Hello!")


a3md = create_server(
    bind_address="127.0.0.1:12345",
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

httpd = ThreadingHTTPServer(("127.0.0.1", 8000), RequestHandler)
httpd_thread = Thread(target=httpd.serve_forever)
httpd_thread.start()

print("Block main thread")
a3md_thread.join()
