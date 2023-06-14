import bluesky.plan_stubs as bps
import pytest
from bluesky import RunEngine
from ophyd.sim import make_fake_device

from dodal.devices.areadetector.plugins.MXSC import PinTipDetect


@pytest.fixture
def fake_pin_tip_detect() -> PinTipDetect:
    FakePinTipDetect = make_fake_device(PinTipDetect)
    pin_tip_detect: PinTipDetect = FakePinTipDetect(name="pin_tip")
    yield pin_tip_detect


def test_given_pin_tip_stays_invalid_when_triggered_then_return_(
    fake_pin_tip_detect: PinTipDetect,
):
    def trigger_and_read():
        yield from bps.abs_set(fake_pin_tip_detect.validity_timeout, 0.01)
        yield from bps.trigger(fake_pin_tip_detect)
        yield from bps.wait()
        return (yield from bps.rd(fake_pin_tip_detect))

    RE = RunEngine(call_returns_result=True)
    result = RE(trigger_and_read())

    assert result.plan_result == fake_pin_tip_detect.INVALID_POSITION


def test_given_pin_tip_invalid_when_triggered_and_set_then_rd_returns_value(
    fake_pin_tip_detect: PinTipDetect,
):
    def trigger_and_read():
        yield from bps.trigger(fake_pin_tip_detect)
        fake_pin_tip_detect.tip_y.sim_put(100)
        fake_pin_tip_detect.tip_x.sim_put(200)
        yield from bps.wait()
        return (yield from bps.rd(fake_pin_tip_detect))

    RE = RunEngine(call_returns_result=True)
    result = RE(trigger_and_read())

    assert result.plan_result == (200, 100)
