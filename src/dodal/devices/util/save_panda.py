import os
import sys
from argparse import ArgumentParser
from typing import cast

from bluesky import RunEngine
from ophyd_async.core import Device, save_device
from ophyd_async.panda import phase_sorter

from dodal.beamlines import module_name_for_beamline
from dodal.utils import make_all_devices


def _save_panda_to_file(RE: RunEngine, panda: Device, path: str):
    def save_to_file():
        yield from save_device(panda, path, sorter=phase_sorter)

    RE(save_to_file())


def _main():
    parser = ArgumentParser(description="Save an ophyd_async device to yaml")
    parser.add_argument(
        "--beamline", help="beamline to save from e.g. i03. Defaults to BEAMLINE"
    )
    parser.add_argument("device_name", help="name of the device e.g. panda")
    parser.add_argument("output_file", help="output filename")
    args = parser.parse_args()
    beamline = args.beamline
    device_name = args.device_name
    output_file = args.output_file

    print(f"Saving to {output_file} from {device_name} on {beamline}")

    if beamline:
        os.environ["BEAMLINE"] = beamline

    RE = RunEngine()

    print("Creating devices...")
    module_name = module_name_for_beamline(beamline)
    devices, exceptions = make_all_devices(
        f"dodal.beamlines.{module_name}", include_skipped=False
    )
    panda = devices[device_name]

    print("Saving to file...")
    _save_panda_to_file(RE, cast(Device, panda), output_file)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
