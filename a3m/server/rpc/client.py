import time

import click
import grpc

from . import a3m_pb2
from . import a3m_pb2_grpc


DEFAULT_SERVER_ADDR = "localhost:7000"


@click.group()
def cli():
    pass


@cli.command()
@click.option("--name", default=str(time.time()))
@click.option("--address", default=DEFAULT_SERVER_ADDR)
@click.argument("url")
def submit(name, address, url):
    click.echo("Submitting...")
    with _get_channel(address) as channel:
        _submit(channel, name, url)


@cli.command()
@click.option("--name", default=str(time.time()))
@click.option("--address", default=DEFAULT_SERVER_ADDR)
@click.argument("url")
def submit_sync(name, address, url):
    click.echo("Submitting and waiting...")
    with _get_channel(address) as channel:
        _submit(channel, name, url, wait=True)


@cli.command()
@click.option("--address", default=DEFAULT_SERVER_ADDR)
@click.argument("package_id")
def status(address, package_id):
    click.echo("Loading status...")
    with _get_channel(address) as channel:
        _status(channel, package_id)


def _get_channel(address):
    return grpc.insecure_channel(
        target=address,
        options=[
            ("grpc.lb_policy_name", "pick_first"),
            ("grpc.enable_retries", 0),
            ("grpc.keepalive_timeout_ms", 10000),
        ],
    )


def _status(channel, package_id):
    stub = a3m_pb2_grpc.TransferStub(channel)
    try:
        resp = stub.Status(a3m_pb2.StatusRequest(id=package_id), timeout=1)
    except grpc.RpcError as err:
        click.echo(
            click.style(f"RPC failed ({err.code()} - {err.details()})", fg="red"),
            err=True,
        )
    else:
        click.echo(a3m_pb2.PackageStatus.Name(resp.status))


def _submit(channel, name, url, wait=False):
    stub = a3m_pb2_grpc.TransferStub(channel)
    try:
        resp = stub.Submit(a3m_pb2.SubmitRequest(name=name, url=url), timeout=1)
    except grpc.RpcError as err:
        click.echo(
            click.style(f"RPC failed ({err.code()} - {err.details()})", fg="red"),
            err=True,
        )
        return

    package_id = resp.id
    click.echo(f"Transfer created: {package_id}")

    if not wait:
        return

    while True:
        time.sleep(2)
        try:
            resp = stub.Status(a3m_pb2.StatusRequest(id=package_id), timeout=1)
        except grpc.RpcError as err:
            click.echo(
                click.style(f"RPC failed ({err.code()} - {err.details()})", fg="red"),
                err=True,
            )
            return
        else:
            if resp.status == a3m_pb2.COMPLETE:
                click.echo("Done!")
                return
            click.echo(
                "Transfer in progress... ({})".format(
                    a3m_pb2.PackageStatus.Name(resp.status)
                )
            )


if __name__ == "__main__":
    # TODO: this could actually be pretty much the example of
    # the a3m cli as long as you can also start up the MCPServer.
    cli()
