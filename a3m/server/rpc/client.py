# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import sys
import time

import grpc

from . import a3m_pb2
from . import a3m_pb2_grpc


DEFAULT_SERVER_ADDR = "localhost:7000"

DEFAULT_URL = "https://github.com/artefactual/archivematica-sampledata/raw/master/SampleTransfers/ZippedBag.zip"


def _get_server_address():
    try:
        return sys.argv[1]
    except IndexError:
        return DEFAULT_SERVER_ADDR


def _submit(stub):
    try:
        resp = stub.Submit(
            a3m_pb2.SubmitRequest(name=str(time.time()), url=DEFAULT_URL), timeout=1
        )
    except grpc.RpcError as err:
        print("RPC failed ({} - {})".format(err.code(), err.details()))
        return

    package_id = resp.id
    print("Transfer created: {}".format(package_id))

    while True:
        time.sleep(2)
        try:
            resp = stub.Status(a3m_pb2.StatusRequest(id=package_id), timeout=1)
        except grpc.RpcError as err:
            print("RPC failed ({} - {})".format(err.code(), err.details()))
            return
        else:
            if resp.status == a3m_pb2.COMPLETE:
                print("Done!")
                return
            print(
                "Transfer in progress... ({})".format(
                    a3m_pb2.PackageStatus.Name(resp.status)
                )
            )


def run():
    address = _get_server_address()
    with grpc.insecure_channel(
        target=address,
        options=[
            ("grpc.lb_policy_name", "pick_first"),
            ("grpc.enable_retries", 0),
            ("grpc.keepalive_timeout_ms", 10000),
        ],
    ) as channel:
        stub = a3m_pb2_grpc.TransferStub(channel)
        _submit(stub)


if __name__ == "__main__":
    # TODO: this could actually be pretty much the example of
    # the a3m cli as long as you can also start up the MCPServer.
    run()
