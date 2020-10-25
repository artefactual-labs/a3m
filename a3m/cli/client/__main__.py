# pylint: disable=no-value-for-parameter
import datetime
import logging
import sys
from typing import Optional

import click
from django.conf import settings
from google.protobuf.descriptor import FieldDescriptor
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from a3m.cli.client.wrapper import ClientWrapper
from a3m.cli.common import init_django
from a3m.cli.common import suppress_warnings
from a3m.server.rpc.client import Client
from a3m.server.rpc.proto import a3m_pb2


@click.command()
@click.argument("uri")
@click.option("--name", help="Name of the package.", metavar="NAME")
@click.option(
    "--address",
    help='a3m server address (form "host:port"), e.g.: "172.26.30.2:12345".',
    metavar="ADDRESS",
)
@click.option(
    "--wait-for-ready", is_flag=True, help="Block until server becomes available."
)
@click.option(
    "--processing-config",
    "-p",
    multiple=True,
    metavar="CONFIG_PAIR",
    help='Processing configuration pair (form "name:value"), e.g.: "normalize=no".',
)
@click.option("--no-input", is_flag=True, help="Disable interactive mode.")
@click.pass_context
def main(ctx, uri, name, address, processing_config, wait_for_ready, no_input):
    """a3m - Lightweight Archivematica.

    Creates an Archival Information Package (AIP) from the contents in URI.

    URI specifies the location of the transfer. Schemes supported are file,
    http and https, e.g. "file:///mnt/disk1/pictures".

    a3m launches its own embedded instance of the engine unless `--address` is
    used to refer to a remote instance. Use `--wait-for-ready` if you want the
    client to block until the server becomes available. If you are running this
    tool in an automated fashion, use `--no-input` to avoid prompts.
    """
    init_django()
    suppress_warnings()

    # Disable logging.
    if not settings.DEBUG:
        logging.disable(sys.maxsize)

    # A3M-TODO: stop forcing users to provide a transfer name.
    if name is None:
        if no_input:
            name = f"transfer.{datetime.datetime.now().timestamp()}"
        else:
            name = click.prompt("Enter transfer name")

    processing_config = _prepare_config(processing_config)

    with ClientWrapper(address, wait_for_ready) as cw:
        resp = cw.client.submit(uri, name, processing_config)
        click.secho(f"AIP {resp.id} is being generated...")

        resp = cw.client.wait_until_complete(resp.id)

        if (status := resp.status) in (
            a3m_pb2.FAILED,
            a3m_pb2.REJECTED,
        ):
            click.secho(
                f"Error processing package ({a3m_pb2.PackageStatus.Name(status)})!",
                fg="red",
            )
            _print_failed_jobs(cw.client, resp.jobs)
            ctx.exit(1)

        click.secho("Processing completed successfully!", fg="green")


def _to_int(value: str) -> Optional[int]:
    try:
        return int(value)
    except ValueError:
        return None


def _prepare_config(user_pairs):
    """Consolidate ``a3m_pb2.ProcessingConfig`` defaults and user-provided.

    A3M-TODO: defaults should be set on the server!

    ``user_pairs`` is a list of strings following the format ``key=value``.
    Those matching processing configuration attributes will be evaluated as
    indicated by the field type, e.g.:

    * ``normalize=yes`` (boolean), or
    * ``aip_compression_level=1`` (integer), or
    * ``aip_compression_algorithm=1`` (enum)
        (it is not possible at the moment to use the enum names)

    A comprehensive list can be found in the definition of the
    ``ProcessingConfig`` message in the proto file.
    """
    config = a3m_pb2.ProcessingConfig(
        assign_uuids_to_directories=True,
        examine_contents=True,
        generate_transfer_structure_report=True,
        document_empty_directories=True,
        extract_packages=True,
        delete_packages_after_extraction=False,
        identify_transfer=True,
        identify_submission_and_metadata=True,
        identify_before_normalization=True,
        normalize=True,
        transcribe_files=True,
        perform_policy_checks_on_originals=True,
        perform_policy_checks_on_preservation_derivatives=True,
        aip_compression_level=1,
        aip_compression_algorithm=a3m_pb2.ProcessingConfig.S7_COPY,
    )
    for item in user_pairs:
        head, sep, tail = item.partition("=")
        if head and sep:
            try:
                field = a3m_pb2.ProcessingConfig.DESCRIPTOR.fields_by_name[head]
            except KeyError:
                continue
            if field.type == FieldDescriptor.TYPE_BOOL:
                enabled = tail.lower() in ("yes", "true", "1", "on")
                setattr(config, head, enabled)
            elif field.type == FieldDescriptor.TYPE_INT32:
                if (value := _to_int(tail)) is not None:
                    setattr(config, head, value)
            elif field.type == FieldDescriptor.TYPE_ENUM:
                if (value := _to_int(tail)) is not None:
                    setattr(config, head, value)
            else:
                raise NotImplementedError(
                    f"{head} has an unsupported type ({field.type})"
                )
    return config


def _print_failed_jobs(client: Client, jobs):
    """Prints failed jobs and associated tasks for a failed package."""
    if not jobs:
        return
    console = Console()
    console.rule("Failed jobs")
    for item in jobs:
        if item.status != item.FAILED:
            continue
        table = Table(expand=True, show_header=True, header_style="bold magenta")
        table.add_column("Job")
        table.add_column("Identifier")
        table.add_column("Link")
        table.add_row(
            f"[bold]{item.name}[/]\n[dim](part of {item.group})[/]",
            item.id,
            item.link_id,
        )
        console.print(table)
        try:
            resp = client.list_tasks(item.id)
        except Exception:
            console.print("Tasks could not be loaded.")
            continue
        for item in resp.tasks:
            content = f"""[bold]Task {item.id}[/]

Module [bold]{item.execution}[/] (with arguments: [dim]{item.arguments}[/])
--- stdout
{item.stdout}
--- stderr
[red]{item.stderr}[/]
"""
            console.print(Panel(content))


if __name__ == "__main__":
    main()
