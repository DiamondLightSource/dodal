import os
from collections.abc import Mapping

import click
from ophyd_async.core import NotConnected

from dodal.beamlines import (
    all_beamline_names,
    import_beamline_module,
)
from dodal.utils import (
    AnyDevice,
    ConnectPolicy,
    DeviceContext,
    DeviceManager,
)

from . import __version__


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, message="%(version)s")
@click.pass_context
def main(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        print("Please invoke subcommand!")


@main.command(name="connect")
@click.argument(
    "beamline",
    type=click.Choice(list(all_beamline_names())),
    required=True,
)
@click.option(
    "-a",
    "--all",
    is_flag=True,
    help="Attempt to connect to devices marked as skipped",
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
def connect(beamline: str, all: bool, sim_backend: bool) -> None:
    """Initialises a beamline module, connects to all devices, reports
    any connection issues."""

    os.environ["BEAMLINE"] = beamline

    module = import_beamline_module(beamline)
    print(f"Attempting connection to {beamline} (using {module.__name__})")

    # Build and attempt to connect to all devices, using a mock connection
    # if instructed
    manager = DeviceManager.find_or_create_for_module(module)
    context = DeviceContext(
        include_skipped=all,
        connect=ConnectPolicy.IMMEDIATE_MOCK
        if sim_backend
        else ConnectPolicy.IMMEDIATE,
    )

    devices, exceptions = manager.build_all(context)

    # Inform user of successful connections
    _report_successful_devices(devices, sim_backend)

    # If exceptions have occurred, this will print details of the relevant PVs
    if len(exceptions) > 0:
        raise NotConnected(exceptions)


def _report_successful_devices(
    devices: Mapping[str, AnyDevice],
    sim_backend: bool,
) -> None:
    sim_statement = " (sim mode)" if sim_backend else ""
    connected_devices = "\n".join(
        sorted([f"\t{device_name}" for device_name in devices.keys()])
    )

    print(f"{len(devices)} devices connected{sim_statement}:")
    print(connected_devices)
