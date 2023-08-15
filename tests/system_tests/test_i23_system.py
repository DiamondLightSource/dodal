import os

from bluesky.run_engine import RunEngine

from dodal.utils import make_all_devices

if __name__ == "__main__":
    """This test runs against the real beamline and confirms that all the devices connect
    i.e. that we match the beamline PVs.

    THIS TEST IS ONLY EXPECTED TO WORK FROM AN I23 WORKSTATION! This is because i23 uses an
    EPICS v4 (pva) device, and no PVA gateways currently exist.

    This is not implemented as a normal pytest test as those tests run using the S03
    EPICS ports and switching ports at runtime is non-trivial
    """
    os.environ["BEAMLINE"] = "i23"
    from dodal.beamlines import i23

    # For i23, need a RunEngine started, as it uses some Ophyd V2 devices which need a bluesky
    # event loop started in order to connect.
    RE = RunEngine()

    print("Making all i23 devices")
    make_all_devices(i23)
    print("Successfully connected")
