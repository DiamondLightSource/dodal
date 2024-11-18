import os
from collections.abc import Mapping

import click
from bluesky.run_engine import RunEngine
from ophyd_async.core import NotConnected
from ophyd_async.plan_stubs import ensure_connected

from dodal.beamlines import all_beamline_names, module_name_for_beamline
from dodal.utils import AnyDevice, filter_ophyd_devices, make_all_devices

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

    module_name = module_name_for_beamline(beamline)
    full_module_path = f"dodal.beamlines.{module_name}"

    # We need to make a RunEngine to allow ophyd-async devices to connect.
    # See https://blueskyproject.io/ophyd-async/main/explanations/event-loop-choice.html
    RE = RunEngine(call_returns_result=True)

    print(f"Attempting connection to {beamline} (using {full_module_path})")

    # Force all devices to be lazy (don't connect to PVs on instantiation) and do
    # connection as an extra step, because the alternatives is handling the fact
    # that only some devices may be lazy.
    devices, instance_exceptions = make_all_devices(
        full_module_path,
        include_skipped=all,
        fake_with_ophyd_sim=sim_backend,
        wait_for_connection=False,
    )
    devices, connect_exceptions = _connect_devices(RE, devices, sim_backend)

    # Inform user of successful connections
    _report_successful_devices(devices, sim_backend)

    # If exceptions have occurred, this will print details of the relevant PVs
    exceptions = {**instance_exceptions, **connect_exceptions}
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


def _connect_devices(
    RE: RunEngine,
    devices: Mapping[str, AnyDevice],
    sim_backend: bool,
) -> tuple[Mapping[str, AnyDevice], Mapping[str, Exception]]:
    ophyd_devices, ophyd_async_devices = filter_ophyd_devices(devices)
    exceptions = {}

    # Connect ophyd devices
    for name, device in ophyd_devices.items():
        try:
            device.wait_for_connection()
        except Exception as ex:
            exceptions[name] = ex

    # Connect ophyd-async devices
    try:
        RE(ensure_connected(*ophyd_async_devices.values(), mock=sim_backend))
    except NotConnected as ex:
        exceptions = {**exceptions, **ex.sub_errors}

    # Only return the subset of devices that haven't raised an exception
    successful_devices = {
        name: device for name, device in devices.items() if name not in exceptions
    }
    return successful_devices, exceptions
