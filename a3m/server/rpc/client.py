import time

import click
import grpc
import tenacity

from . import a3m_pb2
from . import a3m_pb2_grpc


DEFAULT_SERVER_ADDR = "localhost:7000"


@click.group()
def cli():
    pass


@cli.command()
@click.option("--name", default=str(time.time()))
@click.option("--address", default=DEFAULT_SERVER_ADDR)
@click.option("--wait/--no-wait", default=False)
@click.argument("url")
def submit(name, address, wait, url):
    click.echo("🐶 Submitting...")
    with _get_channel(address) as channel:
        _submit(channel, name, url, wait=wait)


@cli.command()
@click.option("--address", default=DEFAULT_SERVER_ADDR)
@click.argument("package_id")
def status(address, package_id):
    click.echo("⌛ Loading status...")
    with _get_channel(address) as channel:
        _status(channel, package_id)


def _get_channel(address):
    return grpc.insecure_channel(
        target=address,
        options=[("grpc.lb_policy_name", "pick_first"), ("grpc.enable_retries", 1)],
    )


def _status(channel, package_id):
    stub = a3m_pb2_grpc.TransferStub(channel)
    try:
        resp = stub.Status(a3m_pb2.StatusRequest(id=package_id), timeout=1)
    except grpc.RpcError as err:
        click.echo(
            click.style(f"⚠️  RPC failed ({err.code()} - {err.details()})", fg="red"),
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
            click.style(f"⚠️  RPC failed ({err.code()} - {err.details()})", fg="red"),
            err=True,
        )
        return

    package_id = resp.id
    click.echo(f"📦 Package created: {package_id}. Processing...")

    if not wait:
        return

    _poll(package_id, stub)


def _poll_retry_reseval(ret):
    if ret == a3m_pb2.PROCESSING:
        return True
    return False


@tenacity.retry(
    wait=tenacity.wait_fixed(1),
    retry=tenacity.retry(
        tenacity.retry_if_result(_poll_retry_reseval)
        | tenacity.retry_if_exception_type()
    ),
)
def _poll(package_id, stub):
    try:
        resp = stub.Status(a3m_pb2.StatusRequest(id=package_id), timeout=1)
    except grpc.RpcError as err:
        click.echo(
            click.style(
                f"⚠️  RPC failed ({err.code()} - {err.details()}) - Retrying...",
                fg="red",
            ),
            err=True,
        )
        raise
    status_name = a3m_pb2.PackageStatus.Name(resp.status)
    if resp.status == a3m_pb2.PROCESSING:
        return resp.status
    if resp.status == a3m_pb2.COMPLETE:
        click.echo(click.style("Done!", fg="green"))
        return resp.status
    click.echo(
        click.style(
            f"⚠️  Error! Last status seen: {status_name} ({resp.job}).", fg="red"
        ),
        err=True,
    )


if __name__ == "__main__":
    cli()
