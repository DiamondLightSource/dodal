import os

from dodal.utils import make_all_devices

if __name__ == "__main__":
    """This test runs against the real beamline and confirms that all the devices connect
    i.e. that we match the beamline PVs. Obviously this must be run on the DLS network
    and could be flaky if parts of the beamline are down for maintenance.

    This is not implemented as a normal pytest test as those tests run using the S03
    EPICS ports and switching ports at runtime is non-trivial
    """
    os.environ["BEAMLINE"] = "i24"
    from dodal.beamlines import i24

    print("Making all i24 devices")
    make_all_devices(i24)
    print("Successfully connected")
