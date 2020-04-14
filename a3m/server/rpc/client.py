# -*- coding: utf-8 -*-
import sys
import time

import grpc

from . import a3m_pb2
from . import a3m_pb2_grpc


DEFAULT_SERVER_ADDR = "localhost:52000"


def _get_server_address():
    try:
        return sys.argv[1]
    except IndexError:
        return DEFAULT_SERVER_ADDR


def _submit(stub):
    try:
        resp = stub.Submit(
            a3m_pb2.SubmitRequest(name=str(time.time()), url="file:///tmp/MARBLES.TGA"),
            timeout=1,
        )
    except grpc.RpcError as err:
        print("RPC failed ({} - {})".format(err.code(), err.details()))
        return

    package_id = resp.id
    print("Transfer created: {}".format(package_id))

    while True:
        try:
            resp = stub.Status(a3m_pb2.StatusRequest(id=package_id), timeout=1,)
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
        time.sleep(1)


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
    run()
