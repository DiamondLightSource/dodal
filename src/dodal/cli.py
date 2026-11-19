import importlib
import os
from collections.abc import Mapping

import click
from bluesky.run_engine import RunEngine
from click.exceptions import ClickException
from ophyd_async.core import NotConnectedError

from dodal.beamlines import all_beamline_names, module_name_for_beamline
from dodal.device_manager import DeviceManager
from dodal.utils import AnyDevice

from . import __version__


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, message="%(version)s")
@click.pass_context
def main(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        print("Please invoke subcommand!")


@main.command(name="describe")
@click.argument(
    "beamline",
    type=click.Choice(list(all_beamline_names())),
    required=True,
)
@click.option("-n", "--name", "device_manager", default="devices")
def describe(beamline: str, device_manager: str) -> None:
    """Initialises a beamline module, gets the docs of all devices and prints them."""
    os.environ["BEAMLINE"] = beamline

    module_name = module_name_for_beamline(beamline)
    full_module_path = f"dodal.beamlines.{module_name}"

    print(f"Analysing {beamline} (using {full_module_path})")

    mod = importlib.import_module(full_module_path)

    if (manager := getattr(mod, device_manager, None)) and isinstance(
        manager, DeviceManager
    ):
        factories = manager.get_all_factories()
    else:
        print(
            f"No device manager named '{device_manager}' found in {mod}, convert the beamline to use device manager"
        )
        return

    for device_name, factory in sorted(factories.items()):
        print(f"{device_name}:")
        print(factory.__doc__)
        print("*****************************************")


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
@click.option("-n", "--name", "device_manager", default="devices")
@click.option(
    "-t",
    "--timeout",
    is_flag=False,
    help="Specify the timeout when connecting devices. Default is 5 seconds.",
    default=5.0,
)
def connect(
    beamline: str, all: bool, sim_backend: bool, device_manager: str, timeout: float
) -> None:
    """Initialises a beamline module, connects to all devices, reports
    any connection issues.
    """
    os.environ["BEAMLINE"] = beamline

    # We need to make a fake path provider for any detectors that need one,
    # it is not used in dodal connect

    module_name = module_name_for_beamline(beamline)
    full_module_path = f"dodal.beamlines.{module_name}"

    # We need to make a RunEngine to allow ophyd-async devices to connect.
    # See https://blueskyproject.io/ophyd-async/main/explanations/event-loop-choice.html
    _run_engine = RunEngine(call_returns_result=True)

    print(f"Attempting connection to {beamline} (using {full_module_path})")

    mod = importlib.import_module(full_module_path)

    # Don't connect devices as they're built and do connection as an extra step,
    # because the alternatives is handling the fact that only some devices may
    # be lazy.

    if (manager := getattr(mod, device_manager, None)) and isinstance(
        manager, DeviceManager
    ):
        devices, instance_exceptions, connect_exceptions = manager.build_and_connect(
            mock=sim_backend,
            timeout=timeout,
        )
    else:
        raise ClickException(
            f"No device manager named '{device_manager}' found in {mod}"
        )

    # Inform user of successful connections
    _report_successful_devices(devices, sim_backend)

    # If exceptions have occurred, this will print details of the relevant PVs
    exceptions = {**instance_exceptions, **connect_exceptions}
    if len(exceptions) > 0:
        raise NotConnectedError(exceptions)


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
