import argparse
import os
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import cast

from bluesky.run_engine import RunEngine
from ophyd_async.core import Device, save_device
from ophyd_async.fastcs.panda import phase_sorter

from dodal.beamlines import module_name_for_beamline
from dodal.utils import make_device


def main(argv: list[str]):
    """CLI Utility to save the panda configuration."""
    parser = ArgumentParser(description="Save an ophyd_async panda to yaml")
    parser.add_argument(
        "--beamline", help="beamline to save from e.g. i03. Defaults to BEAMLINE"
    )
    parser.add_argument(
        "--device-name",
        help='name of the device. The default is "panda"',
        default="panda",
    )
    parser.add_argument(
        "-f",
        "--force",
        action=argparse.BooleanOptionalAction,
        help="Force overwriting an existing file",
    )
    parser.add_argument("output_file", help="output filename")

    # this exit()s with message/help unless args parsed successfully
    args = parser.parse_args(argv[1:])

    beamline = args.beamline
    device_name = args.device_name
    output_file = args.output_file
    force = args.force

    if beamline:
        os.environ["BEAMLINE"] = beamline
    else:
        beamline = os.environ.get("BEAMLINE", None)

    if not beamline:
        sys.stderr.write("BEAMLINE not set and --beamline not specified\n")
        return 1

    if Path(output_file).exists() and not force:
        sys.stderr.write(
            f"Output file {output_file} already exists and --force not specified."
        )
        return 1

    _save_panda(beamline, device_name, output_file)

    print("Done.")
    return 0


def _save_panda(beamline, device_name, output_file):
    RE = RunEngine()
    print("Creating devices...")
    module_name = module_name_for_beamline(beamline)
    try:
        devices = make_device(f"dodal.beamlines.{module_name}", device_name)
    except Exception as error:
        sys.stderr.write(f"Couldn't create device {device_name}: {error}\n")
        sys.exit(1)

    panda = devices[device_name]
    print(f"Saving to {output_file} from {device_name} on {beamline}...")
    _save_panda_to_file(RE, cast(Device, panda), output_file)


def _save_panda_to_file(RE: RunEngine, panda: Device, path: str):
    def save_to_file():
        yield from save_device(panda, path, sorter=phase_sorter)

    RE(save_to_file())


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv))
