import pytest
from ophyd_async.core import set_mock_value

from dodal.common.beamlines.beamline_utils import get_path_provider
from dodal.common.beamlines.commissioning_mode import read_commissioning_mode


@pytest.mark.timeout(2)
@pytest.mark.parametrize("module_and_devices_for_beamline", ["i03"], indirect=True)
def test_i03_initialises_path_provider(module_and_devices_for_beamline):
    assert get_path_provider()


@pytest.mark.timeout(2)
@pytest.mark.parametrize("module_and_devices_for_beamline", ["i03"], indirect=True)
def test_i03_initialises_commissioning_mode_signal(module_and_devices_for_beamline):
    _, devices, __ = module_and_devices_for_beamline
    set_mock_value(devices["baton"].commissioning, True)
    assert read_commissioning_mode()
