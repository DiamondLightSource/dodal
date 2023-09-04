import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd.sim import make_fake_device

from dodal.devices.backlight import Backlight


@pytest.fixture
def fake_backlight() -> Backlight:
    FakeBacklight = make_fake_device(Backlight)
    fake_backlight: Backlight = FakeBacklight(name="backlight")
    return fake_backlight


def test_backlight_can_be_written_and_read_from(fake_backlight: Backlight):
    fake_backlight.pos.sim_put(fake_backlight.IN)
    assert fake_backlight.pos.get() == fake_backlight.IN


def test_when_backlight_out_it_switches_off(fake_backlight: Backlight):
    RE = RunEngine()
    RE(bps.abs_set(fake_backlight, fake_backlight.OUT))
    assert fake_backlight.toggle.get() == "Off"


def test_when_backlight_in_it_switches_on(fake_backlight: Backlight):
    RE = RunEngine()
    RE(bps.abs_set(fake_backlight, fake_backlight.IN))
    assert fake_backlight.toggle.get() == "On"
