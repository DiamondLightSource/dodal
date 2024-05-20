import pytest

from dodal.devices.i24.i24_vgonio import VGonio


@pytest.mark.parametrize("module_and_devices_for_beamline", ["i24"], indirect=True)
def test_device_creation(RE, module_and_devices_for_beamline):
    _, devices = module_and_devices_for_beamline
    vgonio: VGonio = devices["vgonio"]  # type: ignore
    assert vgonio.prefix == "BL24I-MO-VGON-01:"
    assert vgonio.kappa.prefix == "BL24I-MO-VGON-01:KAPPA"
