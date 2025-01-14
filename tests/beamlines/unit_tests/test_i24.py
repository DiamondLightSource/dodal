import pytest

from dodal.devices.i24.vgonio import VerticalGoniometer


@pytest.mark.parametrize("module_and_devices_for_beamline", ["i24"], indirect=True)
def test_device_creation(RE, module_and_devices_for_beamline):
    _, devices, exceptions = module_and_devices_for_beamline
    assert not exceptions
    vgonio: VerticalGoniometer = devices["vgonio"]  # type: ignore

    assert vgonio._name == "vgonio"
    assert vgonio.omega._name == "vgonio-omega"
