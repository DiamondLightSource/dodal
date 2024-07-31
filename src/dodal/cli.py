import os

import click
from bluesky.run_engine import RunEngine
from ophyd_async.core import NotConnected

from dodal.beamlines import all_beamline_names, module_name_for_beamline
from dodal.utils import make_all_devices

from . import __version__
LAB_FLAG = False
LAB_NAME = "p38"

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
    help="collect_factoriesAttempt to connect to devices marked as skipped",
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
    "-l",
    "--lab-mode",
    is_flag=True,
    help="Connect to a lab environment paired with the beamline. For instance i22 and p38",
    default=False   
)
def connect(beamline: str, all: bool, sim_backend: bool, lab_mode: bool) -> None:
    """Initialises a beamline module, connects to all devices, reports
    any connection issues."""
    if lab_mode:
        global LAB_FLAG
        LAB_FLAG = True
        print(f"Lab mode enabled for {beamline}")

    os.environ["BEAMLINE"] = beamline

    module_name = module_name_for_beamline(beamline)
    full_module_path = f"dodal.beamlines.{module_name}"

    # We need to make a RunEngine to allow ophyd-async devices to connect.
    # See https://blueskyproject.io/ophyd-async/main/explanations/event-loop-choice.html
    RunEngine()
    real_connection_target = LAB_NAME if LAB_FLAG else beamline

    print(f"Attempting connection to {real_connection_target} (using {full_module_path})")
    devices, exceptions = make_all_devices(

        full_module_path,
        include_skipped=all,
        fake_with_ophyd_sim=sim_backend,
    )
    sim_statement = " (sim mode)" if sim_backend else ""

    print(f"{len(devices)} devices connected{sim_statement}:")
    connected_devices = "\n".join(
        sorted([f"\t{device_name}" for device_name in devices.keys()])
    )
    print(connected_devices)

    # If exceptions have occurred, this will print details of the relevant PVs
    if len(exceptions) > 0:
        raise NotConnected(exceptions)
