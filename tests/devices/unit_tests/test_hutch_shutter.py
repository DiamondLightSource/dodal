from unittest.mock import call, patch

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
async def fake_shutter(RE) -> HutchShutter:
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
    RE: RunEngine,
):
    set_mock_value(fake_shutter.interlock.status, 0)

    RE(bps.abs_set(fake_shutter, demand, wait=True))

    assert await fake_shutter.status.get_value() == expected_state

    call_list = []
    for i in expected_calls:
        call_list.append(call(i, wait=True))
    mock_shutter_control = get_mock_put(fake_shutter.control)
    mock_shutter_control.assert_has_calls(call_list)


@patch("dodal.devices.hutch_shutter.LOGGER")
@patch("dodal.devices.hutch_shutter.TEST_MODE")
async def test_shutter_does_not_operate_in_test_mode(
    patch_test_mode, patch_log, fake_shutter: HutchShutter, RE: RunEngine
):
    patch_test_mode.return_value = True
    set_mock_value(fake_shutter.interlock.status, 1)  # Optics hutch open
    set_mock_value(fake_shutter.status, ShutterState.CLOSED)

    RE(bps.abs_set(fake_shutter, ShutterDemand.OPEN, wait=True))

    # Assert shutter state didn't change and warning was logged
    patch_log.warning.assert_called_once_with(
        "Running in test mode, will not operate the experiment shutter."
    )
    assert await fake_shutter.status.get_value() == ShutterState.CLOSED
