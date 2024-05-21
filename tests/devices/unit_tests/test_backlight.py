from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine

from dodal.devices.backlight import Backlight


def test_backlight_can_be_written_and_read_from(mock_backlight: Backlight):
    mock_backlight.pos.sim_put(mock_backlight.IN)  # type: ignore
    assert mock_backlight.pos.get() == mock_backlight.IN


def test_when_backlight_out_it_switches_off(mock_backlight: Backlight, RE: RunEngine):
    RE(bps.mv(mock_backlight, mock_backlight.OUT))
    assert mock_backlight.toggle.get() == "Off"


def test_when_backlight_in_it_switches_on(mock_backlight: Backlight, RE: RunEngine):
    RE(bps.mv(mock_backlight, mock_backlight.IN))
    assert mock_backlight.toggle.get() == "On"
