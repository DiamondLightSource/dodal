import os
from collections.abc import Mapping
from pathlib import Path

import click
from bluesky.run_engine import RunEngine
from ophyd_async.core import NotConnected, StaticPathProvider, UUIDFilenameProvider
from ophyd_async.plan_stubs import ensure_connected

from dodal.beamlines import (
    all_beamline_names,
    module_name_for_beamline,
    shared_beamline_modules,
)
from dodal.common.beamlines.beamline_utils import set_path_provider
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
@click.option(
    "-m",
    "--module-only",
    is_flag=True,
    help="If a beamline depends on a shared beamline module, test devices only within "
    "the selected module.",
    default=False,
)
def connect(beamline: str, all: bool, sim_backend: bool, module_only: bool) -> None:
    """Initialises a beamline module, connects to all devices, reports
    any connection issues."""

    os.environ["BEAMLINE"] = beamline

    # We need to make a fake path provider for any detectors that need one,
    # it is not used in dodal connect
    _spoof_path_provider()

    # We need to make a RunEngine to allow ophyd-async devices to connect.
    # See https://blueskyproject.io/ophyd-async/main/explanations/event-loop-choice.html
    RE = RunEngine(call_returns_result=True)

    exceptions = {}

    if module_only:
        beamline_modules = [module_name_for_beamline(beamline)]
    else:
        beamline_modules = shared_beamline_modules(beamline)

    full_module_paths = [
        f"dodal.beamlines.{bl_module}" for bl_module in beamline_modules
    ]
    print(f"Attempting connection to {beamline} (using {full_module_paths})")
    print(shared_beamline_modules)

    # Force all devices to be lazy (don't connect to PVs on instantiation) and do
    # connection as an extra step, because the alternatives is handling the fact
    # that only some devices may be lazy.
    devices, instance_exceptions = make_all_devices(
        full_module_paths,
        include_skipped=all,
        fake_with_ophyd_sim=sim_backend,
        wait_for_connection=False,
    )
    devices, connect_exceptions = _connect_devices(RE, devices, sim_backend)

    # Inform user of successful connections
    _report_successful_devices(devices, sim_backend)

    # If exceptions have occurred, this will print details of the relevant PVs
    e = {**instance_exceptions, **connect_exceptions}
    exceptions = exceptions | e

    print("Finished all device connections.")
    if len(exceptions) > 0:
        print("=" * 100)
        print("Had the following errors:")
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


def _spoof_path_provider() -> None:
    set_path_provider(StaticPathProvider(UUIDFilenameProvider(), Path("/tmp")))
