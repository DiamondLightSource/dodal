import os

from dodal.utils import make_all_devices

if __name__ == "__main__":
    """This test runs against the real beamline and confirms that all the devices connect
    i.e. that we match the beamline PVs. 
    This must be run on the DLS network, 
    behaviour will be flaky when parts of the beamline are down for maintenance.

    This is not implemented as a normal pytest test as those tests run using the s04_1
    EPICS ports and switching ports at runtime is non-trivial
    """

    _beamline_environment_variable = "i04-1"  # N.B. Hyphen not underscore
    os.environ["BEAMLINE"] = _beamline_environment_variable
    from dodal.beamlines import i04_1

    message_template = "Making all %s devices"
    making_all_message = message_template % _beamline_environment_variable
    print(making_all_message)

    make_all_devices(i04_1)
    print("Successfully connected")
 