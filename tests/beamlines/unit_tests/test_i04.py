from dodal.beamlines import beamline_utils, i04
from dodal.utils import make_all_devices


def test_device_creation():
    beamline_utils.clear_devices()
    devices = make_all_devices(i04, fake_with_ophyd_sim=True)
    for device_name in devices.keys():
        assert device_name in beamline_utils.ACTIVE_DEVICES
    assert len(beamline_utils.ACTIVE_DEVICES) == len(devices)
