import pytest
from ophyd.sim import make_fake_device

from dodal.devices.i24.dual_backlight import DualBacklight


@pytest.fixture
def fake_backlight() -> DualBacklight:
    FakeBacklight = make_fake_device(DualBacklight)
    fake_backlight: DualBacklight = FakeBacklight(name="backlight")

    fake_backlight.pos1.zrst.set("Out")
    fake_backlight.pos1.onst.set("In")
    fake_backlight.pos1.twst.set("LoadCheck")
    fake_backlight.pos1.thst.set("OAV2")
    fake_backlight.pos1.frst.set("Diode")
    return fake_backlight


def test_dual_backlight_can_be_written_and_read_from(fake_backlight: DualBacklight):
    fake_backlight.led2.sim_put("ON")
    assert fake_backlight.led2.get() == "ON"
