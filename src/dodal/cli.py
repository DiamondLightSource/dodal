import click
from bluesky.run_engine import RunEngine

from dodal.beamlines import all_beamline_names, module_name_for_beamline
from dodal.utils import make_all_devices

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

    module_name = module_name_for_beamline(beamline)

    RE = RunEngine()  # noqa: F841

    devices = make_all_devices(
        f"dodal.beamlines.{module_name}",
        include_skipped=all,
        fake_with_ophyd_sim=sim_backend,
    )
    sim_statement = "sim mode" if sim_backend else ""
    print(f"{len(devices)} devices connected ({sim_statement}): ")
    print("\n".join([f"\t{key}" for key in devices.keys()]))
