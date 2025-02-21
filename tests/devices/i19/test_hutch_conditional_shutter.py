from unittest.mock import call, patch

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.testing import callback_on_mock_put, get_mock_put, set_mock_value

from dodal.devices.hutch_shutter import (
    ShutterDemand,
    ShutterNotSafeToOperateError,
    ShutterState,
)
from dodal.devices.i19.shutter import (
    HutchConditionalShutter,
    HutchInvalidError,
    HutchState,
)


@pytest.fixture
async def eh2_shutter(RE: RunEngine) -> HutchConditionalShutter:
    shutter = HutchConditionalShutter("", HutchState.EH2, name="mock_shutter")
    await shutter.connect(mock=True)

    def set_status(value: ShutterDemand, *args, **kwargs):
        value_sta = ShutterState.OPEN if value == "Open" else ShutterState.CLOSED
        set_mock_value(shutter.shutter.status, value_sta)

    callback_on_mock_put(shutter.shutter.control, set_status)

    return shutter


async def test_shutter_raises_error_on_set_if_hutch_invalid(
    eh2_shutter: HutchConditionalShutter,
):
    set_mock_value(eh2_shutter.hutch_state, "INVALID")

    with pytest.raises(HutchInvalidError):
        await eh2_shutter.set(ShutterDemand.OPEN)


@patch("dodal.devices.i19.shutter.LOGGER")
async def test_shutter_does_not_operate_for_hutch_not_in_use_and_logs(
    patch_log,
    eh2_shutter: HutchConditionalShutter,
):
    set_mock_value(eh2_shutter.hutch_state, "EH1")

    await eh2_shutter.set(ShutterDemand.OPEN)

    patch_log.warning.assert_called_once()


async def test_shutter_raises_error_for_hutch_in_use_but_not_safe_to_operate(
    eh2_shutter: HutchConditionalShutter,
):
    set_mock_value(eh2_shutter.hutch_state, "EH2")
    set_mock_value(eh2_shutter.shutter.interlock.status, 1)
    assert await eh2_shutter.shutter.interlock.shutter_safe_to_operate() is False

    with pytest.raises(ShutterNotSafeToOperateError):
        await eh2_shutter.set(ShutterDemand.OPEN)


async def test_shutter_operates_correctly_for_hutch_in_use(
    eh2_shutter: HutchConditionalShutter,
):
    set_mock_value(eh2_shutter.hutch_state, "EH2")
    set_mock_value(eh2_shutter.shutter.interlock.status, 0)
    set_mock_value(eh2_shutter.shutter.status, ShutterState.OPEN)

    await eh2_shutter.set(ShutterDemand.CLOSE)

    assert await eh2_shutter.shutter.status.get_value() == ShutterState.CLOSED
    mock_shutter_control = get_mock_put(eh2_shutter.shutter.control)
    mock_shutter_control.assert_has_calls([call(ShutterDemand.CLOSE, wait=True)])
