import importlib

import click

from dodal.beamlines.beamline_utils import wait_for_connection
from dodal.utils import make_all_devices

from . import __version__

__all__ = ["main"]


ALL_BEAMLINES = {
    "i03",
    "i04",
    "i04_1",
    "i20_1",
    "i22",
    "i23",
    "i24",
    "p38",
    "p45",
}


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="dodal")
@click.pass_context
def main(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        print("Please invoke subcommand!")


@main.command(name="connect")
@click.argument("beamline", type=click.Choice(ALL_BEAMLINES), required=True)
@click.option(
    "-a",
    "--all",
    type=bool,
    help="Attempt to connect to all devices, including the ones that are "
    "not connected by default",
    default=False,
)
def connect(beamline: str, all: bool) -> None:
    from bluesky import RunEngine

    RE = RunEngine()  # noqa: F841

    devices = _devices_for_beamline(beamline)
    if all:
        for device in devices.values():
            wait_for_connection(device)


def _devices_for_beamline(beamline: str):
    bl_mod = importlib.import_module("dodal.beamlines." + beamline)
    importlib.reload(bl_mod)
    return make_all_devices(bl_mod)


# test with: python -m dodal
if __name__ == "__main__":
    main()
