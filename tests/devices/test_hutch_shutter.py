from unittest.mock import call, patch

import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    callback_on_mock_put,
    get_mock_put,
    init_devices,
    set_mock_value,
)
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.hutch_shutter import (
    HutchInterlock,
    HutchShutter,
    ShutterDemand,
    ShutterNotSafeToOperateError,
    ShutterState,
)


@pytest.fixture
async def interlock() -> HutchInterlock:
    async with init_devices(mock=True):
        interlock = HutchInterlock(bl_prefix="TEST")
    return interlock


@pytest.fixture
async def fake_shutter_int(interlock: HutchInterlock) -> HutchShutter:
    async with init_devices(mock=True):
        shutter = HutchShutter(bl_prefix="TEST", interlock=interlock)

    def set_status(value: ShutterDemand, *args, **kwargs):
        value_sta = ShutterState.OPEN if value == "Open" else ShutterState.CLOSED
        set_mock_value(shutter.status, value_sta)

    callback_on_mock_put(shutter.control, set_status)

    return shutter


def test_shutter_can_be_created(fake_shutter_int: HutchShutter):
    assert isinstance(fake_shutter_int, HutchShutter)


async def test_interlock_readable(interlock: HutchInterlock):
    await assert_reading(
        interlock,
        {
            f"{interlock.name}-status": partial_reading(0.0),
        },
    )


@pytest.mark.parametrize(
    "readback, expected_state",
    [
        (0.0, True),
        (1.0, False),
        (7.0, False),
    ],
)
async def test_interlock_shutter_safe_to_operate_logic(
    interlock: HutchInterlock,
    readback: float,
    expected_state: bool,
):
    set_mock_value(interlock.status, readback)
    assert await interlock.shutter_safe_to_operate() is expected_state


async def test_shutter_readable(fake_shutter_int: HutchShutter):
    await assert_reading(
        fake_shutter_int,
        {
            f"{fake_shutter_int.name}-status": partial_reading(ShutterState.FAULT),
        },
    )


async def test_shutter_raises_error_on_set_if_hutch_not_interlocked_on_open(
    fake_shutter_int: HutchShutter,
    interlock: HutchInterlock,
):
    set_mock_value(interlock.status, 1)
    assert await interlock.shutter_safe_to_operate() is False

    with pytest.raises(ShutterNotSafeToOperateError):
        await fake_shutter_int.set(ShutterDemand.OPEN)


async def test_shutter_does_not_raise_error_on_set_if_no_interlocked_on_open(
    fake_shutter_int: HutchShutter,
):
    fake_shutter_int.interlock = None
    await fake_shutter_int.set(ShutterDemand.OPEN)
    mock_shutter_control = get_mock_put(fake_shutter_int.control)
    mock_shutter_control.assert_has_calls(
        [call(i) for i in [ShutterDemand.RESET, ShutterDemand.OPEN]]
    )


async def test_shutter_does_not_error_on_close_even_if_hutch_not_interlocked(
    fake_shutter_int: HutchShutter,
    interlock: HutchInterlock,
):
    set_mock_value(interlock.status, 1)
    assert await interlock.shutter_safe_to_operate() is False

    await fake_shutter_int.set(ShutterDemand.CLOSE)


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
    fake_shutter_int: HutchShutter,
    interlock: HutchInterlock,
    run_engine: RunEngine,
):
    set_mock_value(interlock.status, 0)

    run_engine(bps.abs_set(fake_shutter_int, demand, wait=True))

    assert await fake_shutter_int.status.get_value() == expected_state
    mock_shutter_control = get_mock_put(fake_shutter_int.control)
    mock_shutter_control.assert_has_calls([call(i) for i in expected_calls])


@patch("dodal.devices.hutch_shutter.LOGGER")
@patch("dodal.devices.hutch_shutter.TEST_MODE")
async def test_shutter_does_not_operate_in_test_mode(
    patch_test_mode,
    patch_log,
    fake_shutter_int: HutchShutter,
    interlock: HutchInterlock,
    run_engine: RunEngine,
):
    patch_test_mode.return_value = True
    set_mock_value(interlock.status, 1)  # Optics hutch open
    set_mock_value(fake_shutter_int.status, ShutterState.CLOSED)

    run_engine(bps.abs_set(fake_shutter_int, ShutterDemand.OPEN, wait=True))

    # Assert shutter state didn't change and warning was logged
    patch_log.warning.assert_called_once_with(
        "Running in test mode, will not operate the experiment shutter."
    )
    assert await fake_shutter_int.status.get_value() == ShutterState.CLOSED
