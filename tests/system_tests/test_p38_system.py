import os

from dodal.utils import make_all_devices

if __name__ == "__main__":
    """This test runs against the real beamline and confirms that all the devices connect
    i.e. that we match the beamline PVs.
    This must be run on the DLS network,
    behavior will be flaky when parts of the beamline are down for maintenance.
    """

    os.environ["BEAMLINE"] = "p38"
    from dodal.beamlines import p38

    print("Making all p38 devices")
    make_all_devices(p38)
    print("Successfully connected")
