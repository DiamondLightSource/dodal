import os
import sys
from argparse import ArgumentParser
from typing import cast

from bluesky import RunEngine
from ophyd_async.core import Device, save_device
from ophyd_async.panda import phase_sorter

from dodal.beamlines import module_name_for_beamline
from dodal.utils import make_all_devices


def main():
    """CLI Utility to save ophyd_async devices. This is originally intended to save the
    panda configuration but should work with other devices too."""
    parser = ArgumentParser(description="Save an ophyd_async device to yaml")
    parser.add_argument(
        "--beamline", help="beamline to save from e.g. i03. Defaults to BEAMLINE"
    )
    parser.add_argument("device_name", help="name of the device e.g. panda")
    parser.add_argument("output_file", help="output filename")

    # this exit()s with message/help unless args parsed successfully
    args = parser.parse_args()

    beamline = args.beamline
    device_name = args.device_name
    output_file = args.output_file

    if beamline:
        os.environ["BEAMLINE"] = beamline
    else:
        beamline = os.environ.get("BEAMLINE", None)

    if not beamline:
        sys.stderr.write("BEAMLINE not set and --beamline not specified\n")
        return 1

    _save_panda(beamline, device_name, output_file)

    print("Done.")
    return 0


def _save_panda(beamline, device_name, output_file):
    RE = RunEngine()
    print("Creating devices...")
    module_name = module_name_for_beamline(beamline)
    devices, exceptions = make_all_devices(
        f"dodal.beamlines.{module_name}", include_skipped=False
    )

    if error := exceptions.get(device_name, None):
        sys.stderr.write(f"Couldn't create device {device_name}: {error}\n")
        sys.exit(1)

    panda = devices[device_name]
    print(f"Saving to {output_file} from {device_name} on {beamline}...")
    _save_panda_to_file(RE, cast(Device, panda), output_file)


def _save_panda_to_file(RE: RunEngine, panda: Device, path: str):
    def save_to_file():
        yield from save_device(panda, path, sorter=phase_sorter)

    RE(save_to_file())


if __name__ == "__main__":
    sys.exit(main())
