import argparse
import importlib
import os
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import cast

from bluesky.run_engine import RunEngine
from ophyd_async.core import Device, YamlSettingsProvider
from ophyd_async.plan_stubs import (
    store_settings,
)

from dodal.beamlines import module_name_for_beamline
from dodal.device_manager import DeviceFactory, DeviceManager


def main(argv: list[str] | None = None):
    """CLI Utility to save the panda configuration."""
    parser = ArgumentParser(description="Save an ophyd_async panda to yaml")
    parser.add_argument(
        "--beamline", help="Beamline to save from e.g. i03. Defaults to BEAMLINE"
    )
    parser.add_argument(
        "--device-name",
        help='Name of the device. The default is "panda"',
        default="panda",
    )
    parser.add_argument(
        "--output-file",
        help="Path to output file, including filename, eg '/scratch/panda_settings'. '.yaml' is appended to the file name automatically",
        required=True,
    )
    parser.add_argument(
        "-f",
        "--force",
        action=argparse.BooleanOptionalAction,
        help="Force overwriting an existing file",
    )

    # this exit()s with message/help unless args parsed successfully
    args = parser.parse_args(argv)

    beamline = args.beamline
    device_name = args.device_name
    output_file = args.output_file
    force = args.force

    p = Path(output_file)
    output_directory, file_name = str(p.parent), str(p.name)

    if beamline:
        os.environ["BEAMLINE"] = beamline
    else:
        beamline = os.environ.get("BEAMLINE", None)

    if not beamline:
        sys.stderr.write("BEAMLINE not set and --beamline not specified\n")
        return 1

    if Path(f"{output_directory}/{file_name}").exists() and not force:
        sys.stderr.write(
            f"Output file {output_directory}/{file_name} already exists and --force not specified."
        )
        return 1

    _save_panda(beamline, device_name, output_directory, file_name)

    print("Done.")
    return 0


def _build_panda(beamline, device_name) -> Device:
    print(f"Building {device_name} for beamline {beamline}")
    module_name = module_name_for_beamline(beamline)
    mod = importlib.import_module("dodal.beamlines." + module_name)
    device_manager: DeviceManager = mod.devices
    return cast(DeviceFactory, device_manager[device_name]).build(
        connect_immediately=True
    )


def _save_panda(beamline, device_name, output_directory, file_name):
    run_engine = RunEngine()

    try:
        panda = _build_panda(beamline, device_name)
    except Exception as error:
        sys.stderr.write(f"Couldn't create device {device_name}: {error}\n")
        sys.exit(1)

    print(
        f"Saving to {output_directory}/{file_name} from {device_name} on {beamline}..."
    )
    _save_panda_to_yaml(run_engine, cast(Device, panda), file_name, output_directory)


def _save_panda_to_yaml(
    run_engine: RunEngine, panda: Device, file_name: str, output_directory: str
):
    def save_to_file():
        provider = YamlSettingsProvider(output_directory)
        yield from store_settings(provider, file_name, panda)

    run_engine(save_to_file())


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
