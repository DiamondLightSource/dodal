from unittest.mock import call

import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.testing import (
    callback_on_mock_put,
    get_mock_put,
    set_mock_value,
)

from dodal.devices.hutch_shutter import (
    HutchShutter,
    ShutterDemand,
    ShutterNotSafeToOperateError,
    ShutterState,
)


@pytest.fixture
async def fake_shutter() -> HutchShutter:
    RunEngine()
    shutter = HutchShutter("", name="fake_shutter")
    await shutter.connect(mock=True)

    def set_status(value: ShutterDemand, *args, **kwargs):
        value_sta = ShutterState.OPEN if value == "Open" else ShutterState.CLOSED
        set_mock_value(shutter.status, value_sta)

    callback_on_mock_put(shutter.control, set_status)

    return shutter


def test_shutter_can_be_created(fake_shutter: HutchShutter):
    assert isinstance(fake_shutter, HutchShutter)


async def test_shutter_raises_error_on_set_if_hutch_not_interlocked(
    fake_shutter: HutchShutter,
):
    set_mock_value(fake_shutter.interlock.status, 1)
    assert await fake_shutter.interlock.shutter_safe_to_operate() is False

    with pytest.raises(ShutterNotSafeToOperateError):
        await fake_shutter.set(ShutterDemand.CLOSE)


@pytest.mark.parametrize(
    "demand, expected_calls, expected_state",
    [
        (
            ShutterDemand.OPEN,
            [ShutterDemand.RESET, ShutterDemand.OPEN],
            ShutterState.OPEN,
        ),
        (ShutterDemand.CLOSE, [ShutterDemand.CLOSE], ShutterState.CLOSED),
    ],
)
async def test_shutter_operations(
    demand: ShutterDemand,
    expected_calls: list,
    expected_state: ShutterState,
    fake_shutter: HutchShutter,
    RE,
):
    set_mock_value(fake_shutter.interlock.status, 0)

    RE(bps.abs_set(fake_shutter, demand, wait=True))

    assert await fake_shutter.status.get_value() == expected_state

    call_list = []
    for i in expected_calls:
        call_list.append(call(i, wait=True))
    mock_shutter_control = get_mock_put(fake_shutter.control)
    mock_shutter_control.assert_has_calls(call_list)
