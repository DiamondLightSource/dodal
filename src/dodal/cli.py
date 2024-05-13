import importlib

import click

from dodal.beamlines import ALL_BEAMLINES
from dodal.beamlines.beamline_utils import (
    DEFAULT_CONNECTION_TIMEOUT,
    wait_for_connection,
)
from dodal.utils import make_all_devices

from . import __version__


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="dodal")
@click.pass_context
def main(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        print("Please invoke subcommand!")


@main.command(name="connect")
@click.argument("beamline", type=click.Choice(list(ALL_BEAMLINES)), required=True)
@click.option(
    "-a",
    "--all",
    is_flag=True,
    help="Attempt to connect to all devices, including the ones that are "
    "not connected by default",
    default=False,
)
@click.option(
    "-s",
    "--sim-backend",
    is_flag=True,
    help="Connect to a sim backend, this initializes all device objects but does not "
    "attempt any I/O. Useful as a a dry-run.",
    default=False,
)
@click.option(
    "-t",
    "--timeout",
    type=float,
    help="Connection timeout in seconds",
    default=DEFAULT_CONNECTION_TIMEOUT,
)
def connect(beamline: str, all: bool, sim_backend: bool, timeout: float) -> None:
    """Initialises a beamline module, connects to all devices, reports
    any connection issues"""

    from bluesky import RunEngine

    RE = RunEngine()  # noqa: F841

    devices = _devices_for_beamline(
        beamline,
        include_skipped=all,
        fake_with_ophyd_sim=sim_backend,
    )
    if all:
        for device in devices.values():
            wait_for_connection(
                device,
                timeout=timeout,
                sim=sim_backend,
            )
    sim_statement = "sim mode" if sim_backend else ""
    print(f"{len(devices)} devices connected ({sim_statement}): ")
    print("\n".join([f"\t{key}" for key in devices.keys()]))


def _devices_for_beamline(
    beamline: str,
    include_skipped: bool,
    fake_with_ophyd_sim: bool,
):
    bl_mod = importlib.import_module("dodal.beamlines." + beamline)
    importlib.reload(bl_mod)
    return make_all_devices(
        bl_mod,
        include_skipped=include_skipped,
        fake_with_ophyd_sim=fake_with_ophyd_sim,
    )
