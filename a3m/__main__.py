# pylint: disable=no-value-for-parameter
import os

import click


@click.command()
@click.option("--mode", type=click.Choice(["rpc", "enduro"]), default="rpc")
def service(mode):
    # A3M-TODO: write a click.Choice for enums?
    try:
        mode = ExecutionMode.__members__[mode.upper()]
    except KeyError:
        raise click.UsageError(f"{mode} is not a valid execution mode")
    main(mode=mode)


if __name__ == "__main__":
    # Set up Django here, since we don't use apps.get_model in our app.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "a3m.settings.common")
    import django

    django.setup()
    from a3m.server.mcp import main
    from a3m.server.mcp import ExecutionMode

    service()
