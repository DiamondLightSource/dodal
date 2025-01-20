import pytest

from dodal.beamlines import i24
from dodal.common.beamlines import beamline_utils
from dodal.devices.i24.vgonio import VerticalGoniometer


def test_list():
    beamline_utils.clear_devices()
    i24.zebra(wait_for_connection=False, fake_with_ophyd_sim=True)
    i24.pmac(wait_for_connection=False, fake_with_ophyd_sim=True)
    i24.vgonio(wait_for_connection=False, fake_with_ophyd_sim=True)
    assert beamline_utils.list_active_devices() == [
        "zebra",
        "pmac",
        "vgonio",
    ]


@pytest.mark.parametrize("module_and_devices_for_beamline", ["i24"], indirect=True)
def test_device_creation(RE, module_and_devices_for_beamline):
    _, devices, exceptions = module_and_devices_for_beamline
    assert not exceptions
    vgonio: VerticalGoniometer = devices["vgonio"]  # type: ignore

    assert vgonio._name == "vgonio"
    assert vgonio.omega._name == "vgonio-omega"
