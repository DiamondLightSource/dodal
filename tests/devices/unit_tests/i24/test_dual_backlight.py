from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine

from dodal.devices.i24.dual_backlight import DualBacklight


def test_dual_backlight_can_be_written_and_read_from(
    mock_dual_backlight: DualBacklight,
):
    mock_dual_backlight.led2.sim_put("OFF")  # type: ignore
    assert mock_dual_backlight.led2.get() == "OFF"


def test_backlight_position(mock_dual_backlight: DualBacklight):
    mock_dual_backlight.pos1.pos_level.sim_put(mock_dual_backlight.IN)  # type: ignore
    assert mock_dual_backlight.pos1.pos_level.get() == "In"


def test_when_led1_out_it_switches_off(
    mock_dual_backlight: DualBacklight, RE: RunEngine
):
    RE(bps.mv(mock_dual_backlight, mock_dual_backlight.OUT))
    assert mock_dual_backlight.led1.get() == "OFF"


def test_when_led1_not_out_it_switches_on(
    mock_dual_backlight: DualBacklight, RE: RunEngine
):
    RE(bps.mv(mock_dual_backlight, "OAV2"))
    assert mock_dual_backlight.led1.get() == "ON"


def test_led2_independent_from_led1_position(
    mock_dual_backlight: DualBacklight, RE: RunEngine
):
    mock_dual_backlight.led2.sim_put("OFF")  # type: ignore
    RE(bps.abs_set(mock_dual_backlight, mock_dual_backlight.IN, wait=True))
    assert mock_dual_backlight.led1.get() == "ON"
    assert mock_dual_backlight.led2.get() == "OFF"
