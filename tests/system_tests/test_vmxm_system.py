import os

from bluesky.run_engine import RunEngine

from dodal.utils import make_all_devices

if __name__ == "__main__":
    """This test runs against the real beamline and confirms that all the devices connect
    i.e. that we match the beamline PVs.
    """
    os.environ["BEAMLINE"] = "i02-1"
    from dodal.beamlines import vmxm

    RE = RunEngine()

    print("Making all VMXm devices")
    make_all_devices(vmxm)
    print("Successfully connected")