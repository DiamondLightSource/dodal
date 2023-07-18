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


def trigger_and_read(fake_pin_tip_detect, value_to_set_during_trigger=None):
    yield from bps.trigger(fake_pin_tip_detect)
    if value_to_set_during_trigger:
        fake_pin_tip_detect.tip_y.sim_put(value_to_set_during_trigger[1])
        fake_pin_tip_detect.tip_x.sim_put(value_to_set_during_trigger[0])
    yield from bps.wait()
    return (yield from bps.rd(fake_pin_tip_detect))


def test_given_pin_tip_stays_invalid_when_triggered_then_return_(
    fake_pin_tip_detect: PinTipDetect,
):
    def set_small_timeout_then_trigger_and_read():
        yield from bps.abs_set(fake_pin_tip_detect.validity_timeout, 0.01)
        return (yield from trigger_and_read(fake_pin_tip_detect))

    RE = RunEngine(call_returns_result=True)
    result = RE(set_small_timeout_then_trigger_and_read())

    assert result.plan_result == fake_pin_tip_detect.INVALID_POSITION


def test_given_pin_tip_invalid_when_triggered_and_set_then_rd_returns_value(
    fake_pin_tip_detect: PinTipDetect,
):
    RE = RunEngine(call_returns_result=True)
    result = RE(trigger_and_read(fake_pin_tip_detect, (200, 100)))

    assert result.plan_result == (200, 100)


def test_given_pin_tip_found_before_timeout_then_timeout_status_cleaned_up_and_tip_value_remains(
    fake_pin_tip_detect: PinTipDetect,
):
    RE = RunEngine(call_returns_result=True)
    RE(trigger_and_read(fake_pin_tip_detect, (100, 200)))
    assert fake_pin_tip_detect._timeout_status.done
    assert fake_pin_tip_detect.triggered_tip.get() == (100, 200)
