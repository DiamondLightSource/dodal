import os
from unittest.mock import patch

from dodal.devices.i24.i24_vgonio import VGonio

with patch.dict(os.environ, {"BEAMLINE": "i24"}, clear=True):
    from dodal.beamlines import beamline_utils, i24
    from dodal.utils import make_all_devices


def setup_module():
    beamline_utils.set_beamline("i24")


def test_device_creation():
    devices = make_all_devices(i24, fake_with_ophyd_sim=True)
    assert len(devices) > 0
    for device_name in devices.keys():
        assert device_name in beamline_utils.ACTIVE_DEVICES
    assert len(beamline_utils.ACTIVE_DEVICES) == len(devices)

    vgonio: VGonio = beamline_utils.ACTIVE_DEVICES["vgonio"]
    assert vgonio.prefix == "BL24I-MO-VGON-01:"
    assert vgonio.kappa.prefix == "BL24I-MO-VGON-01:KAPPA"


def teardown_module():
    beamline_utils.set_beamline("i24")
    beamline_utils.clear_devices()
