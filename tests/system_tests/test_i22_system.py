import os

from bluesky import RunEngine

from dodal.utils import make_all_devices

if __name__ == "__main__":
    """This test runs against the real beamline and confirms that all the devices connect
    i.e. that we match the beamline PVs.
    This must be run on the DLS network,
    behavior will be flaky when parts of the beamline are down for maintenance.
    """

    os.environ["BEAMLINE"] = "i22"
    from dodal.beamlines import i22

    print("Making all i22 devices")
    RE = RunEngine()
    make_all_devices(i22)
    print("Successfully connected")
