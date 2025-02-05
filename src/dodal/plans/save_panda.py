import argparse
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
from dodal.utils import make_device


def main(argv: list[str]):
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
    args = parser.parse_args(argv[1:])

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


def _save_panda(beamline, device_name, output_directory, file_name):
    RE = RunEngine()
    print("Creating devices...")
    module_name = module_name_for_beamline(beamline)
    try:
        devices = make_device(
            f"dodal.beamlines.{module_name}", device_name, connect_immediately=True
        )
    except Exception as error:
        sys.stderr.write(f"Couldn't create device {device_name}: {error}\n")
        sys.exit(1)

    panda = devices[device_name]
    print(
        f"Saving to {output_directory}/{file_name} from {device_name} on {beamline}..."
    )
    _save_panda_to_yaml(RE, cast(Device, panda), file_name, output_directory)


def _save_panda_to_yaml(
    RE: RunEngine, panda: Device, file_name: str, output_directory: str
):
    def save_to_file():
        provider = YamlSettingsProvider(output_directory)
        yield from store_settings(provider, file_name, panda)

    RE(save_to_file())


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv))
