from typing import Generator, List, Tuple

import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine
from ophyd.sim import make_fake_device

from dodal.devices.areadetector.plugins.MXSC import (
    PinTipDetect,
    statistics_of_positions,
)


@pytest.fixture
def fake_pin_tip_detect() -> Generator[PinTipDetect, None, None]:
    FakePinTipDetect = make_fake_device(PinTipDetect)
    pin_tip_detect: PinTipDetect = FakePinTipDetect(name="pin_tip")
    pin_tip_detect.settle_time_s.set(0).wait()
    yield pin_tip_detect


def trigger_and_read(
    fake_pin_tip_detect, values_to_set_during_trigger: List[Tuple] = None
):
    yield from bps.trigger(fake_pin_tip_detect)
    if values_to_set_during_trigger:
        for position in values_to_set_during_trigger:
            fake_pin_tip_detect.tip_y.sim_put(position[1])  # type: ignore
            fake_pin_tip_detect.tip_x.sim_put(position[0])  # type: ignore
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
    result = RE(trigger_and_read(fake_pin_tip_detect, [(200, 100)]))

    assert result.plan_result == (200, 100)


def test_given_pin_tip_found_before_timeout_then_timeout_status_cleaned_up_and_tip_value_remains(
    fake_pin_tip_detect: PinTipDetect,
):
    RE = RunEngine(call_returns_result=True)
    RE(trigger_and_read(fake_pin_tip_detect, [(100, 200)]))
    # A success should clear up the timeout status but it may clear it up slightly later
    # so we need the small timeout to avoid the race condition
    fake_pin_tip_detect._timeout_status.wait(0.01)
    assert fake_pin_tip_detect.triggered_tip.get() == (100, 200)


def test_median_of_positions_calculated_correctly():
    test = [(1, 2), (1, 5), (3, 3)]

    actual_med, _ = statistics_of_positions(test)

    assert actual_med == (1, 3)


def test_standard_dev_of_positions_calculated_correctly():
    test = [(1, 2), (1, 3)]

    _, actual_std = statistics_of_positions(test)

    assert actual_std == (0, 0.5)


def test_given_multiple_tips_found_then_running_median_calculated(
    fake_pin_tip_detect: PinTipDetect,
):
    fake_pin_tip_detect.settle_time_s.set(0.1).wait()

    RE = RunEngine(call_returns_result=True)
    RE(trigger_and_read(fake_pin_tip_detect, [(100, 200), (50, 60), (400, 800)]))

    assert fake_pin_tip_detect.triggered_tip.get() == (100, 200)


def trigger_and_read_twice(
    fake_pin_tip_detect: PinTipDetect, first_values: List[Tuple], second_value: Tuple
):
    yield from trigger_and_read(fake_pin_tip_detect, first_values)
    fake_pin_tip_detect.tip_y.sim_put(second_value[1])  # type: ignore
    fake_pin_tip_detect.tip_x.sim_put(second_value[0])  # type: ignore
    return (yield from trigger_and_read(fake_pin_tip_detect, []))


def test_given_median_previously_calculated_when_triggered_again_then_only_calculated_on_new_values(
    fake_pin_tip_detect: PinTipDetect,
):
    fake_pin_tip_detect.settle_time_s.set(0.1).wait()

    RE = RunEngine(call_returns_result=True)

    def my_plan():
        tip_pos = yield from trigger_and_read_twice(
            fake_pin_tip_detect, [(10, 20), (1, 3), (4, 8)], (100, 200)
        )
        assert tip_pos == (100, 200)

    RE(my_plan())


def test_given_previous_tip_found_when_this_tip_not_found_then_returns_invalid(
    fake_pin_tip_detect: PinTipDetect,
):
    fake_pin_tip_detect.settle_time_s.set(0.1).wait()
    fake_pin_tip_detect.validity_timeout.set(0.5).wait()

    RE = RunEngine(call_returns_result=True)

    def my_plan():
        tip_pos = yield from trigger_and_read_twice(
            fake_pin_tip_detect, [(10, 20), (1, 3), (4, 8)], (-1, -1)
        )
        assert tip_pos == (-1, -1)

    RE(my_plan())
